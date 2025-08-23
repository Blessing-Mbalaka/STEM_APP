# stem_app/views/login.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import get_user_model, authenticate, login, logout

import json

User = get_user_model()

# -------- Helpers --------
def _parse_request_data(request):
    """Parse JSON or form data safely."""
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}
    return request.POST

# -------- Page view --------
def login_page(request):
    """Render your existing login.html."""
    return render(request, "login.html")

# -------- API views --------
@ensure_csrf_cookie
def api_me(request):
    """Return current user info (and set csrftoken cookie)."""
    if request.user.is_authenticated:
        u = request.user
        return JsonResponse({
            "authenticated": True,
            "username": u.username,
            "email": u.email,
            "display_name": getattr(u, "display_name", "") or u.username,
        })
    return JsonResponse({"authenticated": False})

@require_POST
def api_register(request):
    """Create account, then auto-login."""
    data = _parse_request_data(request)
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    email = (data.get("email") or "").strip()
    display_name = (data.get("display_name") or "").strip()

    if not username or not password:
        return JsonResponse({"error": "username and password required"}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "username already taken"}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    if display_name:
        user.display_name = display_name
        user.save(update_fields=["display_name"])

    login(request, user)
    return JsonResponse({"ok": True, "username": user.username})

@require_POST
def api_login(request):
    """Session login."""
    data = _parse_request_data(request)
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    login(request, user)
    return JsonResponse({"ok": True, "username": user.username})

@require_POST
def api_logout(request):
    """Session logout."""
    logout(request)
    return JsonResponse({"ok": True})
