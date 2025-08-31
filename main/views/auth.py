# main/views/auth.py
from __future__ import annotations

import json
from random import randint

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse, HttpRequest
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.db.models import Sum, Avg
from django.views.decorators.http import require_http_methods

User = get_user_model()


@ensure_csrf_cookie
def login_page(request: HttpRequest):
    """Render the custom login page and set csrftoken cookie."""
    from django.shortcuts import render
    return render(request, "Login.html")


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
        return JsonResponse({"error": "Account disabled"}, status=403)

    login(request, user)
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
@csrf_protect
def api_register(request: HttpRequest):
    """Create an account. Username optional; derived from email/display_name if omitted."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    email = (payload.get("email") or "").strip()
    first_name = (payload.get("first_name") or payload.get("firstName") or "").strip()
    last_name = (payload.get("last_name") or payload.get("lastName") or "").strip()
    display_name = (payload.get("display_name") or f"{first_name} {last_name}" or username or (email.split("@")[0] if email else "")).strip()

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

    # Enforce unique email if provided
    if email and User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"error": "Email already in use"}, status=409)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or None,
    )
    # Set names if provided
    if hasattr(user, "first_name") and first_name:
        user.first_name = first_name
    if hasattr(user, "last_name") and last_name:
        user.last_name = last_name
    if hasattr(user, "display_name"):
        user.display_name = display_name
    user.save()

    login(request, user)  # auto-login after register
    return JsonResponse({"ok": True})


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

    data = {
        "authenticated": True,
        "id": user.id,
        "username": user.username,
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
