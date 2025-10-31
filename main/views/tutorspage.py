# main/views/classes.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from ..models import ClassSession, Reservation
from django.utils.timezone import now
from django.utils import timezone
from django.conf import settings
from main.views.courses import user_can_manage_tutor_admin
import json

def Tutors(request):
    return render(request, "Tutors.html")

@require_GET
def api__list(request):
    """
    GET /api/classes
    Return session payload expected by the frontend.
    """
    qs = ClassSession.objects.select_related("course", "created_by").order_by("starts_at")
    data = []
    for s in qs[:200]:
        reserved_count = Reservation.objects.filter(session=s).count()
        user_reserved = request.user.is_authenticated and Reservation.objects.filter(user=request.user, session=s).exists()
        # Frontend treats remaining==null as unlimited — keep None to avoid "full"
        remaining = None
        data.append({
            "id": s.id,
            "title": getattr(s, "title", "") or (s.course.title if getattr(s, "course", None) else ""),
            "course": s.course.title if getattr(s, "course", None) else None,
            "location": getattr(s, "location", "") or "",
            "starts_at": s.starts_at.isoformat() if getattr(s, "starts_at", None) else None,
            "ends_at": s.ends_at.isoformat() if getattr(s, "ends_at", None) else None,
            "capacity": getattr(s, "capacity", None),
            "reserved_count": reserved_count,
            "user_reserved": user_reserved,
            "reserved": user_reserved,
            "tutor": (getattr(s, "created_by", None) and (getattr(s.created_by, "display_name", None) or getattr(s.created_by, "username", None))) or "",
            "tutor_id": getattr(s, "created_by_id", None),
            "when": s.starts_at.isoformat() if getattr(s, "starts_at", None) else "",
            "subject": s.course.title if getattr(s, "course", None) else (getattr(s, "title", "") or ""),
            "remaining": remaining,
        })
    return JsonResponse({"results": data})

@login_required
@require_http_methods(["POST"])
def api_class_reserve(request, pk: int):
    """
    POST /api/classes/<id>/reserve
    Create reservation for current user. Do NOT block on capacity (frontend treats classes unlimited).
    """
    session = get_object_or_404(ClassSession, pk=pk)

    # Treat None or 0 as unlimited capacity (do not block)
    capacity = getattr(session, "capacity", None)
    limited = bool(capacity and capacity > 0)

    if limited:
        reserved_count = Reservation.objects.filter(session=session).count()
        if reserved_count >= capacity:
            return JsonResponse({"error": "Class is full"}, status=400)

    # idempotent create
    Reservation.objects.get_or_create(user=request.user, session=session)
    return JsonResponse({"ok": True})

@login_required
@require_http_methods(["DELETE"])
def api_class_unreserve(request, pk: int):
    session = get_object_or_404(ClassSession, pk=pk)
    Reservation.objects.filter(user=request.user, session=session).delete()
    return JsonResponse({"ok": True})

@login_required
@require_GET
def api_me_classes(request):
    """
    Return current user's reservations mapped to frontend format.
    """
    qs = Reservation.objects.select_related("session__course", "session__created_by").filter(user=request.user).order_by("-id")
    results = []
    for r in qs:
        s = r.session
        results.append({
            "id": s.id,
            "title": getattr(s, "title", "") or (s.course.title if getattr(s, "course", None) else ""),
            "tutor": (getattr(s, "created_by", None) and (getattr(s.created_by, "display_name", None) or getattr(s.created_by, "username", None))) or "",
            "date": s.starts_at.isoformat() if getattr(s, "starts_at", None) else "",
            "subject": s.course.title if getattr(s, "course", None) else (getattr(s, "title", "") or ""),
            "status": "upcoming",
            "meetingLink": getattr(s, "location", "") or "#",
        })
    return JsonResponse({"results": results})


# ---------- Tutor scheduling APIs ----------
@require_http_methods(["GET", "POST"])
@login_required
def api_tutor_classes(request):
    # gate by settings like tutor admin
    if not user_can_manage_tutor_admin(request.user):
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
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    s = get_object_or_404(ClassSession, pk=pk)
    s.delete()
    return JsonResponse({"ok": True})
