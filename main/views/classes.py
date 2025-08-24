# main/views/classes.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from ..models import ClassSession, Reservation
from django.utils.timezone import now
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
            "starts_at": s.starts_at.isoformat(),
            "ends_at": s.ends_at.isoformat(),
            "capacity": s.capacity,
            "reserved": Reservation.objects.filter(session=s).count(),
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
