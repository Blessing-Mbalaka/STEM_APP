# main/views/classes.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from ..models import ClassSession, Reservation
from django.utils.timezone import now
from django.utils import timezone
from django.conf import settings
import json

def classes(request):
    return render(request, "Classes.html")

@require_GET
def api_classes_list(request):
    """
    GET /api/classes?course=<id>&from=<YYYY-MM-DD>&to=<YYYY-MM-DD>
    Returns simple session cards for your UI.
    """
    qs = ClassSession.objects.select_related("course").order_by("starts_at")
    course_id = request.GET.get("course")
    if course_id:
        qs = qs.filter(course_id=course_id)

    # (Optional) date filters — keep very permissive for now
    # You can add proper parsing later if you want
    data = []
    for s in qs[:200]:
        data.append({
            "id": s.id,
            "title": getattr(s, "title", s.course.title if s.course else "Class"),
            "course": s.course.title if s.course else None,
            "location": s.location,
            "starts_at": s.starts_at.isoformat(),
            "ends_at": s.ends_at.isoformat(),
            "capacity": s.capacity,
            "reserved": Reservation.objects.filter(session=s).count(),
            "tutor": (s.created_by.display_name or s.created_by.username) if s.created_by else None,
        })
    return JsonResponse({"results": data})

@login_required
@require_http_methods(["POST"])
def api_class_reserve(request, pk: int):
    """
    POST /api/classes/<id>/reserve
    Creates a reservation for the current user if space exists.
    """
    session = get_object_or_404(ClassSession, pk=pk)
    # capacity check (very simple)
    if Reservation.objects.filter(session=session).count() >= session.capacity:
        return JsonResponse({"error": "Class is full"}, status=400)

    # ensure only one reservation per user per session
    Reservation.objects.get_or_create(user=request.user, session=session)
    return JsonResponse({"ok": True})

@login_required
@require_http_methods(["DELETE"])
def api_class_unreserve(request, pk: int):
    """
    DELETE /api/classes/<id>/reserve
    """
    session = get_object_or_404(ClassSession, pk=pk)
    Reservation.objects.filter(user=request.user, session=session).delete()
    return JsonResponse({"ok": True})

@login_required
@require_GET
def api_me_classes(request):
    """
    GET /api/me/classes
    """
    reservations = Reservation.objects.select_related("session", "session__course").filter(user=request.user)
    data = []
    for r in reservations:
        s = r.session
        data.append({
            "id": s.id,
            "title": getattr(s, "title", s.course.title if s.course else "Class"),
            "course": s.course.title if s.course else None,
            "starts_at": s.starts_at.isoformat(),
            "ends_at": s.ends_at.isoformat(),
        })
    return JsonResponse({"results": data})


# ---------- Tutor scheduling APIs ----------
@require_http_methods(["GET", "POST"])
@login_required
def api_tutor_classes(request):
    # gate by settings like tutor admin
    req_staff = getattr(settings, 'TUTOR_ADMIN_REQUIRE_STAFF', False)
    req_tutor = getattr(settings, 'TUTOR_ADMIN_REQUIRE_TUTOR', False)
    if (req_staff and not request.user.is_staff) or (req_tutor and not (getattr(request.user, 'is_tutor', False) or request.user.is_staff)):
        return JsonResponse({"error": "forbidden"}, status=403)

    if request.method == "GET":
        qs = ClassSession.objects.select_related('course').order_by('starts_at')
        course_id = request.GET.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        results = [{
            "id": s.id,
            "title": s.title,
            "course_id": s.course_id,
            "course": s.course.title if s.course else None,
            "starts_at": s.starts_at.isoformat(),
            "ends_at": s.ends_at.isoformat(),
            "location": s.location,
            "capacity": s.capacity,
            "description": s.description,
            "tutor": (s.created_by.display_name or s.created_by.username) if s.created_by else None,
        } for s in qs[:300]]
        return JsonResponse({"results": results})

    # POST: create
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    from main.models.course import Course
    try:
        course_id = int(payload.get('course_id'))
    except Exception:
        return JsonResponse({"error": "course_id required"}, status=400)
    course = get_object_or_404(Course, pk=course_id)

    title = (payload.get('title') or course.title or 'Class').strip()
    starts = payload.get('starts_at') or ''
    ends = payload.get('ends_at') or ''
    try:
        # parse ISO; make aware
        sdt = timezone.make_aware(timezone.datetime.fromisoformat(starts)) if 'T' in starts else timezone.make_aware(timezone.datetime.strptime(starts, '%Y-%m-%d %H:%M'))
        edt = timezone.make_aware(timezone.datetime.fromisoformat(ends)) if 'T' in ends else timezone.make_aware(timezone.datetime.strptime(ends, '%Y-%m-%d %H:%M'))
    except Exception:
        return JsonResponse({"error": "starts_at/ends_at must be ISO (YYYY-MM-DDTHH:MM) or 'YYYY-MM-DD HH:MM'"}, status=400)
    loc = payload.get('location') or ''
    try:
        cap = int(payload.get('capacity') or 0)
    except Exception:
        cap = 0
    desc = payload.get('description') or ''
    s = ClassSession.objects.create(course=course, title=title, starts_at=sdt, ends_at=edt, location=loc, capacity=cap, description=desc, created_by=request.user)
    return JsonResponse({"id": s.id})


@require_http_methods(["DELETE"]) 
@login_required
def api_tutor_class_detail(request, pk: int):
    req_staff = getattr(settings, 'TUTOR_ADMIN_REQUIRE_STAFF', False)
    req_tutor = getattr(settings, 'TUTOR_ADMIN_REQUIRE_TUTOR', False)
    if (req_staff and not request.user.is_staff) or (req_tutor and not (getattr(request.user, 'is_tutor', False) or request.user.is_staff)):
        return JsonResponse({"error": "forbidden"}, status=403)
    s = get_object_or_404(ClassSession, pk=pk)
    s.delete()
    return JsonResponse({"ok": True})
