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

@login_required
def admin_resources_page(request: HttpRequest):
    if not _require_admin(request):
        return HttpResponseForbidden("Forbidden")
    return render(request, "AdminResources.html")


@require_http_methods(["GET", "POST"])
@login_required
def api_admin_resource_categories(request: HttpRequest):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.resource import ResourceCategory, ResourceDocument
    if request.method == "GET":
        terms = ResourceDocument.term_options()
        results = []
        for cat in ResourceCategory.objects.all().order_by("name"):
            counts = {}
            total = 0
            for term in terms:
                value = term["value"]
                count = cat.documents.filter(term=value).count()
                counts[value] = count
                total += count
            results.append({
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "description": cat.description,
                "total": total,
                "counts": counts,
            })
        return JsonResponse({"results": results, "terms": terms})
    import json
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "name required"}, status=400)
    description = (payload.get("description") or "").strip()
    from django.db import IntegrityError
    try:
        category = ResourceCategory.objects.create(
            name=name,
            description=description,
            created_by=request.user,
        )
    except IntegrityError:
        return JsonResponse({"error": "Category already exists"}, status=400)
    return JsonResponse({"id": category.id, "name": category.name})


@require_http_methods(["PATCH", "DELETE"])
@login_required
def api_admin_resource_category_detail(request: HttpRequest, pk: int):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.resource import ResourceCategory
    category = get_object_or_404(ResourceCategory, pk=pk)
    if request.method == "DELETE":
        category.delete()
        return JsonResponse({"ok": True})
    import json
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    changed = False
    if "name" in payload:
        new_name = (payload.get("name") or "").strip()
        if new_name:
            category.name = new_name
            changed = True
    if "description" in payload:
        category.description = (payload.get("description") or "").strip()
        changed = True
    if changed:
        category.save()
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
@login_required
def api_admin_resource_documents(request: HttpRequest):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.resource import ResourceCategory, ResourceDocument
    category_id = request.GET.get("category") or request.GET.get("category_id")
    if not category_id:
        return JsonResponse({"error": "category required"}, status=400)
    category = get_object_or_404(ResourceCategory, pk=category_id)
    terms = ResourceDocument.term_options()
    grouped = {term["value"]: [] for term in terms}
    for doc in category.documents.all().order_by("term", "-created_at", "title"):
        entry = {
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "term": doc.term,
            "term_label": doc.get_term_display(),
            "file": request.build_absolute_uri(doc.file.url) if doc.file else "",
            "uploaded_at": doc.created_at.isoformat(),
            "original_filename": doc.original_filename,
        }
        grouped.setdefault(doc.term, []).append(entry)
    return JsonResponse({
        "category": {"id": category.id, "name": category.name, "description": category.description},
        "terms": terms,
        "documents": grouped,
    })


@require_http_methods(["POST"])
@login_required
def api_admin_resource_upload(request: HttpRequest):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.resource import ResourceCategory, ResourceDocument
    import os
    category_id = request.POST.get("category") or request.POST.get("category_id")
    term = (request.POST.get("term") or ResourceDocument.TERM_OTHER).strip()
    description = (request.POST.get("description") or "").strip()
    title_override = (request.POST.get("title") or "").strip()
    if not category_id:
        return JsonResponse({"error": "category required"}, status=400)
    category = get_object_or_404(ResourceCategory, pk=category_id)
    valid_terms = {value for value, _ in ResourceDocument.TERM_CHOICES}
    if term not in valid_terms:
        return JsonResponse({"error": "invalid term"}, status=400)
    files = request.FILES.getlist("files") or ([])
    single = request.FILES.get("file")
    if single and not files:
        files = [single]
    if not files:
        return JsonResponse({"error": "No files uploaded"}, status=400)
    uploaded = []
    for idx, upload in enumerate(files, start=1):
        original = upload.name
        if title_override:
            title = title_override if len(files) == 1 else f"{title_override} ({idx})"
        else:
            title = os.path.splitext(original)[0].replace('_', ' ').strip() or "Resource"
        doc = ResourceDocument.objects.create(
            category=category,
            title=title,
            description=description,
            term=term,
            file=upload,
            uploaded_by=request.user,
            original_filename=original,
        )
        uploaded.append({
            "id": doc.id,
            "title": doc.title,
            "term": doc.term,
            "file": request.build_absolute_uri(doc.file.url) if doc.file else "",
        })
    return JsonResponse({"uploaded": uploaded})


@require_http_methods(["PATCH", "DELETE"])
@login_required
def api_admin_resource_document_detail(request: HttpRequest, pk: int):
    if not _require_admin(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.resource import ResourceDocument, ResourceCategory
    doc = get_object_or_404(ResourceDocument, pk=pk)
    if request.method == "DELETE":
        try:
            if doc.file:
                doc.file.delete(save=False)
        except Exception:
            pass
        doc.delete()
        return JsonResponse({"ok": True})
    import json
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    changed = False
    if "title" in payload:
        new_title = (payload.get("title") or "").strip()
        if new_title:
            doc.title = new_title
            changed = True
    if "description" in payload:
        doc.description = (payload.get("description") or "").strip()
        changed = True
    if "term" in payload:
        new_term = payload.get("term")
        if new_term in {value for value, _ in ResourceDocument.TERM_CHOICES}:
            doc.term = new_term
            changed = True
    if "category" in payload:
        new_category_id = payload.get("category")
        if new_category_id:
            category = get_object_or_404(ResourceCategory, pk=new_category_id)
            doc.category = category
            changed = True
    if changed:
        doc.save()
    return JsonResponse({"ok": True})
