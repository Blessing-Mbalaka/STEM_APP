# main/views/auth.py
from __future__ import annotations

import json
from random import randint

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse, HttpRequest
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
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
    display_name = (payload.get("display_name") or username or (email.split("@")[0] if email else "")).strip()

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

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or None,
    )
    if hasattr(user, "first_name"):
        user.first_name = display_name
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


@require_http_methods(["GET", "PATCH"])
@csrf_protect  # required for PATCH
def api_me(request: HttpRequest):
    """Return or update minimal profile for the logged-in user."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=200)

    if request.method == "PATCH":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        for field in ["first_name", "last_name", "email"]:
            if field in payload and hasattr(user, field):
                setattr(user, field, (payload[field] or "").strip())
        user.save()

    data = {
        "authenticated": True,
        "id": user.id,
        "username": user.username,
        "first_name": getattr(user, "first_name", "") or "",
        "last_name": getattr(user, "last_name", "") or "",
        "email": getattr(user, "email", "") or "",
    }
    return JsonResponse(data)
