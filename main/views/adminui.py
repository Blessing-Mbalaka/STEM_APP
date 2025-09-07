from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model

User = get_user_model()


def _require_admin(request: HttpRequest):
    if not request.user.is_authenticated:
        return False
    # Allow superusers and staff to access admin UI
    return bool(getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False))


@login_required
def admin_users_page(request: HttpRequest):
    if not _require_admin(request):
        return HttpResponseForbidden("Forbidden")
    return render(request, "AdminUsers.html")


@require_http_methods(["GET"])
@login_required
def api_admin_users(request: HttpRequest):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    q = (request.GET.get('q') or '').strip()
    role = (request.GET.get('role') or '').strip().lower()  # tutor|student|staff|all
    status = (request.GET.get('status') or '').strip().lower()  # active|inactive|all
    qs = User.objects.all().order_by('-date_joined')
    if q:
        qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q)
    if role == 'tutor':
        qs = qs.filter(is_tutor=True)
    elif role == 'staff':
        qs = qs.filter(is_staff=True)
    elif role == 'student':
        qs = qs.filter(is_tutor=False, is_staff=False)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    data = [{
        'id': u.id,
        'username': u.username,
        'email': u.email or '',
        'display_name': getattr(u, 'display_name', '') or '',
        'is_active': bool(u.is_active),
        'is_staff': bool(u.is_staff),
        'is_superuser': bool(u.is_superuser),
        'is_tutor': bool(getattr(u, 'is_tutor', False)),
        'joined': getattr(u, 'date_joined', None).isoformat() if getattr(u, 'date_joined', None) else ''
    } for u in qs[:500]]
    return JsonResponse({"results": data})


@require_http_methods(["PATCH"])
@login_required
def api_admin_user_update(request: HttpRequest, pk: int):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    import json
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    u = get_object_or_404(User, pk=pk)
    changed = False
    if 'is_active' in payload:
        u.is_active = bool(payload.get('is_active')); changed = True
    if 'is_tutor' in payload and hasattr(u, 'is_tutor'):
        u.is_tutor = bool(payload.get('is_tutor')); changed = True
    # Only superusers may toggle staff
    if 'is_staff' in payload and getattr(request.user, 'is_superuser', False):
        u.is_staff = bool(payload.get('is_staff')); changed = True
    if 'reset_password' in payload and payload.get('reset_password'):
        newp = payload.get('new_password') or None
        if newp and len(newp) >= 6:
            u.set_password(newp); changed = True
    if changed:
        u.save()
    return JsonResponse({"ok": True})


@login_required
def admin_approvals_page(request: HttpRequest):
    if not _require_admin(request):
        return HttpResponseForbidden("Forbidden")
    return render(request, "AdminApprovals.html")


@login_required
def admin_dashboard_page(request: HttpRequest):
    if not _require_admin(request):
        return HttpResponseForbidden("Forbidden")
    return render(request, "Administrator.html")


def administrator_login_page(request: HttpRequest):
    # A simple login page without role toggles; client-side posts to /api/auth/login
    from django.shortcuts import render, redirect
    if request.user.is_authenticated and _require_admin(request):
        return redirect('/administrator/')
    return render(request, "AdministratorLogin.html")


@require_http_methods(["GET"])
@login_required
def api_admin_content_pending(request: HttpRequest):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.course import Course
    from main.models.game import Game
    courses = list(Course.objects.filter(is_active=False).order_by('-created_at').values('id','title','subject','level','created_at'))
    games = list(Game.objects.filter(is_active=False).order_by('-created_at').values('id','title','category','difficulty','created_at'))
    return JsonResponse({"courses": courses, "games": games})


@require_http_methods(["PATCH"])
@login_required
def api_admin_course_approve(request: HttpRequest, pk: int):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.course import Course
    c = get_object_or_404(Course, pk=pk)
    c.is_active = True
    c.save()
    return JsonResponse({"ok": True})


@require_http_methods(["PATCH"])
@login_required
def api_admin_game_approve(request: HttpRequest, pk: int):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.game import Game
    g = get_object_or_404(Game, pk=pk)
    g.is_active = True
    g.save()
    return JsonResponse({"ok": True})
