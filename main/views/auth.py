# main/views/auth.py
from __future__ import annotations

import json
from random import randint

import os

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.db.models import Sum, Avg
from django.views.decorators.http import require_http_methods
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from main.utils.roles import (
    get_primary_role,
    get_user_roles,
    ROLE_ADMIN,
    ROLE_TUTOR,
)
from ..models.tutor import TutorApplication, TutorApplicationDocument

ALLOWED_DOC_EXTENSIONS = {".pdf"}


def _is_allowed_file(upload) -> bool:
    if not upload:
        return False
    ext = os.path.splitext(getattr(upload, "name", "") or "")[1].lower()
    return ext in ALLOWED_DOC_EXTENSIONS

User = get_user_model()


@ensure_csrf_cookie
def login_page(request: HttpRequest):
    """Render the custom login page and set csrftoken cookie. Redirect if already logged in."""
    from django.shortcuts import render, redirect
    if request.user.is_authenticated:
        role = get_primary_role(request.user)
        if role == ROLE_ADMIN:
            target = "/administrator/"
        elif role == ROLE_TUTOR:
            target = "/tutor/admin/"
        else:
            target = "/index/"
        return redirect(target)
    return render(request, "login.html")


def awaiting_activation_page(request: HttpRequest):
    """Simple informational page for pending tutors."""
    return render(request, "AwaitingActivation.html")


@require_http_methods(["POST"])
@csrf_protect
def api_login(request: HttpRequest):
    """Login with either username OR email + password."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    identifier = (payload.get("username")
                  or payload.get("email")
                  or payload.get("identifier")
                  or "").strip()
    password = payload.get("password") or ""

    if not identifier or not password:
        return JsonResponse({"error": "username/email and password required"}, status=400)

    user = None
    if "@" in identifier:
        try:
            u = User.objects.get(email__iexact=identifier)
            user = authenticate(request, username=u.username, password=password)
        except User.DoesNotExist:
            user = None
    else:
        user = authenticate(request, username=identifier, password=password)

    if not user:
        return JsonResponse({"error": "Invalid credentials"}, status=401)
    if not user.is_active:
        redirect_url = "/awaiting-activation/"
        return JsonResponse(
            {
                "error": "Account pending activation by an administrator",
                "redirect": redirect_url,
            },
            status=403,
        )

    login(request, user)
    role = get_primary_role(user)
    if role == ROLE_ADMIN:
        target = "/administrator/"
    elif role == ROLE_TUTOR:
        target = "/tutor/admin/"
    else:
        target = "/index/"
    return JsonResponse({"ok": True, "redirect": target, "role": role})


@require_http_methods(["POST"])
@csrf_protect
def api_register(request: HttpRequest):
    """Create an account. Supports JSON and multipart (for tutor docs)."""
    is_multipart = request.content_type and "multipart/form-data" in request.content_type.lower()
    content_type = (request.content_type or "").lower()
    is_multipart = "multipart/form-data" in content_type
    if is_multipart:
        data = request.POST
        id_document = request.FILES.get("id_document")
        qualification_documents = list(request.FILES.getlist("qualification_documents"))
        supporting_documents = list(request.FILES.getlist("supporting_documents"))
        sace_documents = list(request.FILES.getlist("sace_documents"))
    else:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid payload"}, status=400)
        id_document = None
        qualification_documents = []
        supporting_documents = []
        sace_documents = []

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip()
    first_name = (data.get("first_name") or data.get("firstName") or "").strip()
    last_name = (data.get("last_name") or data.get("lastName") or "").strip()
    display_name = (
        data.get("display_name")
        or f"{first_name} {last_name}"
        or username
        or (email.split("@")[0] if email else "")
    ).strip()
    role = (data.get("role") or "").strip().lower()
    motivation = (data.get("motivation") or data.get("tutor_motivation") or "").strip()

    if not password:
        return JsonResponse({"error": "password required"}, status=400)

    # derive username if missing
    if not username:
        base = slugify(email.split("@")[0] if email else (display_name or "user"))[:30] or "user"
        candidate = base
        i = 0
        while User.objects.filter(username__iexact=candidate).exists():
            i += 1
            suffix = str(randint(1000, 9999)) if i > 25 else str(i)
            candidate = (base[:30 - len(suffix)]) + suffix
        username = candidate

    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({"error": "Username already taken"}, status=409)

    if email and User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"error": "Email already in use"}, status=409)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or None,
    )
    # Set names if provided
    fields_to_update = []
    if hasattr(user, "first_name") and first_name:
        user.first_name = first_name
        fields_to_update.append("first_name")
    if hasattr(user, "last_name") and last_name:
        user.last_name = last_name
        fields_to_update.append("last_name")
    if hasattr(user, "display_name") and display_name:
        user.display_name = display_name
        fields_to_update.append("display_name")

    # Auto-activate students; tutors require approval
    if role == "tutor":
        validation_errors = {}
        if not is_multipart:
            validation_errors["documents"] = "Attach your tutor documents (identity document and qualifications)."
        if not id_document:
            validation_errors["id_document"] = "Identity document (PDF) is required."
        elif not _is_allowed_file(id_document):
            validation_errors["id_document"] = "Identity document must be a PDF file."

        if not qualification_documents:
            validation_errors["qualification_documents"] = "Upload at least one qualification as a PDF."
        else:
            for doc in qualification_documents:
                if not _is_allowed_file(doc):
                    validation_errors["qualification_documents"] = "All qualification documents must be PDF files."
                    break

        for doc in supporting_documents:
            if not _is_allowed_file(doc):
                validation_errors["supporting_documents"] = "Supporting documents must be PDF files."
                break

        for doc in sace_documents:
            if not _is_allowed_file(doc):
                validation_errors["sace_documents"] = "SACE certificates must be PDF files."
                break

        if validation_errors:
            user.delete()
            return JsonResponse(
                {"error": "Tutor application incomplete.", "details": validation_errors},
                status=400,
            )

        user.is_active = False
        if hasattr(user, "is_tutor"):
            user.is_tutor = False
        user.save(update_fields=["is_active", "is_tutor", *fields_to_update])

        application = TutorApplication.objects.create(user=user, motivation=motivation)

        TutorApplicationDocument.objects.create(
            application=application,
            file=id_document,
            original_name=getattr(id_document, "name", ""),
            doc_type=TutorApplicationDocument.DOC_ID,
        )
        for doc in qualification_documents:
            TutorApplicationDocument.objects.create(
                application=application,
                file=doc,
                original_name=getattr(doc, "name", ""),
                doc_type=TutorApplicationDocument.DOC_QUALIFICATION,
            )
        for doc in supporting_documents:
            TutorApplicationDocument.objects.create(
                application=application,
                file=doc,
                original_name=getattr(doc, "name", ""),
                doc_type=TutorApplicationDocument.DOC_SUPPORTING,
            )
        for doc in sace_documents:
            TutorApplicationDocument.objects.create(
                application=application,
                file=doc,
                original_name=getattr(doc, "name", ""),
                doc_type=TutorApplicationDocument.DOC_SACE,
            )
        pending_msg = "Registration successful. Your tutor application is pending review."
        return JsonResponse(
            {
                "ok": True,
                "message": pending_msg,
                "redirect": "/awaiting-activation/",
                "role": get_primary_role(user),
            }
        )

    # Default: student
    user.is_active = True
    user.save(update_fields=["is_active", *fields_to_update] if fields_to_update else ["is_active"])
    login(request, user)
    role_name = get_primary_role(user)
    if role_name == ROLE_ADMIN:
        redirect_to = "/administrator/"
    elif role_name == ROLE_TUTOR:
        redirect_to = "/tutor/admin/"
    else:
        redirect_to = "/index/"
    return JsonResponse({"ok": True, "redirect": redirect_to, "role": role_name})


@require_http_methods(["POST"])
@csrf_protect
def api_logout(request: HttpRequest):
    """Logout current user."""
    logout(request)
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
@csrf_protect
def api_delete_account(request: HttpRequest):
    """Delete the authenticated user's account and all related records."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)
    # Optional: simple confirmation flag
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}
    confirm = str(payload.get("confirm") or "").lower()
    if confirm not in {"yes", "true", "confirm", "delete"}:
        return JsonResponse({"error": "Confirmation required"}, status=400)

    # Delete the user (cascades to Profile and related FK with on_delete)
    user.delete()
    return JsonResponse({"ok": True})

# ---- Change password page and API ----
from django.shortcuts import render

def change_password_page(request: HttpRequest):
    return render(request, "ChangePassword.html")

@require_http_methods(["POST"])
@csrf_protect
def api_change_password(request: HttpRequest):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    old = data.get("old_password") or ""
    new = data.get("new_password") or ""
    confirm = data.get("confirm_password") or ""
    if not user.check_password(old):
        return JsonResponse({"error": "Current password is incorrect"}, status=400)
    if not new or len(new) < 6:
        return JsonResponse({"error": "New password must be at least 6 characters"}, status=400)
    if new != confirm:
        return JsonResponse({"error": "Passwords do not match"}, status=400)
    user.set_password(new)
    user.save()
    # Re-login to keep session
    login(request, user)
    # Role-based redirect target
    role = get_primary_role(user)
    if role == ROLE_ADMIN:
        target = "/administrator/"
    elif role == ROLE_TUTOR:
        target = "/tutor/admin/"
    else:
        target = "/index/"
    return JsonResponse({"ok": True, "redirect": target, "role": role})


# ---- Forgot/Reset password (unauthenticated flow) ----
@ensure_csrf_cookie
def forgot_password_page(request: HttpRequest):
    from django.shortcuts import render
    return render(request, "ForgotPassword.html")


@require_http_methods(["POST"])
@csrf_protect
def api_forgot_password(request: HttpRequest):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    identifier = (payload.get("email") or payload.get("username") or payload.get("identifier") or "").strip()
    if not identifier:
        return JsonResponse({"error": "Email or username required"}, status=400)

    # Find user by email or username
    user = None
    try:
        if "@" in identifier:
            user = User.objects.get(email__iexact=identifier)
        else:
            user = User.objects.get(username__iexact=identifier)
    except User.DoesNotExist:
        # Always return ok to avoid user enumeration
        return JsonResponse({"ok": True, "message": "If the account exists, a reset link has been sent."})

    # Generate token and build link
    token_gen = PasswordResetTokenGenerator()
    token = token_gen.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    # absolute link for console and development
    try:
        base = request.build_absolute_uri('/')[:-1]
    except Exception:
        base = ''
    link = f"{base}/reset-password/{uidb64}/{token}/"
    # Print to terminal for now
    print(f"[DEV] Password reset link for {user.username}: {link}")

    return JsonResponse({"ok": True, "message": "If the account exists, a reset link has been sent."})


@ensure_csrf_cookie
def reset_password_page(request: HttpRequest, uidb64: str, token: str):
    from django.shortcuts import render
    # We pass through; actual validation occurs on POST to API
    return render(request, "ResetPassword.html", {"uidb64": uidb64, "token": token})


@require_http_methods(["POST"])
@csrf_protect
def api_reset_password(request: HttpRequest):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    uidb64 = (payload.get("uidb64") or "").strip()
    token = (payload.get("token") or "").strip()
    new_password = payload.get("new_password") or ""
    confirm_password = payload.get("confirm_password") or ""
    if not uidb64 or not token:
        return JsonResponse({"error": "Invalid reset link"}, status=400)
    if not new_password or len(new_password) < 6:
        return JsonResponse({"error": "Password must be at least 6 characters"}, status=400)
    if new_password != confirm_password:
        return JsonResponse({"error": "Passwords do not match"}, status=400)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        return JsonResponse({"error": "Invalid reset link"}, status=400)

    token_gen = PasswordResetTokenGenerator()
    if not token_gen.check_token(user, token):
        return JsonResponse({"error": "Reset link has expired or is invalid"}, status=400)

    user.set_password(new_password)
    user.save()
    return JsonResponse({"ok": True})

@require_http_methods(["GET", "PATCH"])
@ensure_csrf_cookie  # set csrftoken on GET; PATCH still enforced by middleware
def api_me(request: HttpRequest):
    """Return or update minimal profile for the logged-in user."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=200)

    # import inside to avoid circulars
    from main.models.user import Profile
    from main.models.game import GameScore

    if request.method == "PATCH":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Update core user fields (support camelCase from frontend)
        field_map = {
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
            "firstName": "first_name",
            "lastName": "last_name",
        }
        # Email uniqueness check
        if "email" in payload:
            new_email = (payload.get("email") or "").strip()
            if new_email and new_email.lower() != (getattr(user, "email", "") or "").lower():
                if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
                    return JsonResponse({"error": "Email already in use"}, status=409)
                user.email = new_email
        for incoming, model_field in field_map.items():
            if incoming in payload and model_field != "email" and hasattr(user, model_field):
                setattr(user, model_field, (payload[incoming] or "").strip())
        user.save()

        # Ensure profile exists
        profile, _ = Profile.objects.get_or_create(user=user)
        # Map payload keys -> profile attributes
        mapping = {
            "phone": "phone",
            "dob": "dob",
            "gender": "gender",
            "bio": "bio",
            "school": "school",
            "grade": "grade",
            "academicGoals": "academic_goals",
            "languagePref": "language_pref",
            "notificationPref": "notification_pref",
            "studyTimes": "study_times",
            "stream": "stream",
            "learningStyles": "learning_styles",
        }
        # Special handling for date + json fields
        from datetime import datetime
        def _parse_date(val: str):
            if not val:
                return None
            s = str(val).strip().replace("/", "-")
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y"):
                try:
                    return datetime.strptime(s[:19], fmt).date()
                except Exception:
                    continue
            return None

        for key, attr in mapping.items():
            if key not in payload:
                continue
            if attr == "dob":
                dt = _parse_date(payload.get(key))
                if payload.get(key) and dt is None:
                    return JsonResponse({"error": "dob must be YYYY-MM-DD"}, status=400)
                setattr(profile, attr, dt)
            elif attr == "learning_styles":
                ls = payload.get(key)
                if ls is None:
                    profile.learning_styles = []
                elif isinstance(ls, list):
                    profile.learning_styles = ls
                else:
                    return JsonResponse({"error": "learningStyles must be a list"}, status=400)
            else:
                setattr(profile, attr, payload.get(key) or "")
        profile.save()

    # compute totals for games
    scores_qs = GameScore.objects.filter(user=user)
    agg_points = scores_qs.aggregate(s=Sum("points_awarded"))
    total_points = int(agg_points.get("s") or 0)
    agg_avg = scores_qs.aggregate(a=Avg("score_percent"))
    avg_score = float(agg_avg.get("a") or 0.0)
    completed_sessions = scores_qs.count()

    # simple streak: consecutive days ending today
    streak_days = 0
    try:
        from django.utils import timezone
        dates = list(scores_qs.values_list("created_at", flat=True))
        if dates:
            # normalize to dates only
            days = sorted({ d.astimezone(timezone.get_current_timezone()).date() for d in dates }, reverse=True)
            from datetime import timedelta, date
            today = timezone.localdate()
            expected = today
            for d in days:
                if d == expected:
                    streak_days += 1
                    expected = expected - timedelta(days=1)
                elif d > expected:
                    continue
                else:
                    break
    except Exception:
        streak_days = 0

    # Ensure profile exists and include extended fields
    profile, _ = Profile.objects.get_or_create(user=user)

    roles = sorted(get_user_roles(user))
    primary_role = get_primary_role(user)

    data = {
        "authenticated": True,
        "id": user.id,
        "username": user.username,
        "is_staff": bool(getattr(user, "is_staff", False)),
        "is_tutor": bool(getattr(user, "is_tutor", False)),
        "role": primary_role,
        "roles": roles,
        "first_name": getattr(user, "first_name", "") or "",
        "last_name": getattr(user, "last_name", "") or "",
        # camelCase copies for frontend compatibility
        "firstName": getattr(user, "first_name", "") or "",
        "lastName": getattr(user, "last_name", "") or "",
        "email": getattr(user, "email", "") or "",
        "display_name": getattr(user, "display_name", "") or getattr(user, "first_name", "") or user.username,
        "total_points": total_points,
        "completedSessions": completed_sessions,
        "quizScore": round(avg_score, 1) if completed_sessions else None,
        "streakDays": streak_days,
        # extended profile fields
        "phone": getattr(profile, "phone", "") or "",
        "dob": getattr(profile, "dob", None).isoformat() if getattr(profile, "dob", None) else "",
        "gender": getattr(profile, "gender", "") or "",
        "bio": getattr(profile, "bio", "") or "",
        "school": getattr(profile, "school", "") or "",
        "grade": getattr(profile, "grade", "") or "",
        "academicGoals": getattr(profile, "academic_goals", "") or "",
        "languagePref": getattr(profile, "language_pref", "") or "",
        "notificationPref": getattr(profile, "notification_pref", "") or "",
        "studyTimes": getattr(profile, "study_times", "") or "",
        "stream": getattr(profile, "stream", "") or "",
        "learningStyles": getattr(profile, "learning_styles", None) or [],
        "avatar_url": (request.build_absolute_uri(profile.avatar.url) if getattr(profile, "avatar", None) and getattr(profile.avatar, "url", None) else ""),
    }
    return JsonResponse(data)

@require_http_methods(["POST"])
@csrf_protect
def api_upload_avatar(request: HttpRequest):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)
    from main.models.user import Profile
    profile, _ = Profile.objects.get_or_create(user=user)
    file = request.FILES.get("avatar")
    if not file:
        return JsonResponse({"error": "No file uploaded"}, status=400)
    # optional: limit size/type
    # If an old avatar exists, delete the previous file to avoid orphan files
    try:
        if profile.avatar and hasattr(profile.avatar, 'name') and profile.avatar.name:
            profile.avatar.delete(save=False)
    except Exception:
        pass
    profile.avatar = file
    profile.save()
    return JsonResponse({"ok": True, "avatar_url": request.build_absolute_uri(profile.avatar.url)})
