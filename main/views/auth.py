# main/views/auth.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout, get_user_model
import json

User = get_user_model()

@ensure_csrf_cookie  # ensures csrftoken cookie is set when page loads
def login_page(request):
    # renders Login.html (your existing page view)
    from django.shortcuts import render
    return render(request, "Login.html")

@require_http_methods(["POST"])
def api_login(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return JsonResponse({"error": "username and password required"}, status=400)

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if not user.is_active:
        return JsonResponse({"error": "Account disabled"}, status=403)

    login(request, user)
    return JsonResponse({"ok": True})

@require_http_methods(["POST"])
def api_register(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    email = (payload.get("email") or "").strip()
    display_name = (payload.get("display_name") or username).strip()

    if not username or not password:
        return JsonResponse({"error": "username and password required"}, status=400)

    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({"error": "Username already taken"}, status=409)

    # Create user (map display_name to your CustomUser fields)
    # Adjust if your CustomUser uses first_name/full_name/display_name fields.
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or None,
    )
    # Optional: set names if your model has them
    if hasattr(user, "first_name"):
        user.first_name = display_name
    if hasattr(user, "display_name"):
        user.display_name = display_name
    user.save()

    # Auto-login after register
    login(request, user)
    return JsonResponse({"ok": True})

@require_http_methods(["POST"])
def api_logout(request):
    logout(request)
    return JsonResponse({"ok": True})

@require_http_methods(["GET", "PATCH"])
def api_me(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=200)

    if request.method == "PATCH":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        # Update a few common fields safely
        for field in ["first_name", "last_name", "email"]:
            if field in payload and hasattr(user, field):
                setattr(user, field, (payload[field] or "").strip())
        user.save()

    # Return a simple profile payload
    data = {
        "authenticated": True,
        "username": user.username,
        "first_name": getattr(user, "first_name", "") or "",
        "last_name": getattr(user, "last_name", "") or "",
        "email": getattr(user, "email", "") or "",
        "id": user.id,
    }
    return JsonResponse(data)
