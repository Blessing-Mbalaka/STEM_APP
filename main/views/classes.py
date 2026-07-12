# main/views/classes.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from ..models import ClassSession, Reservation, Message, CustomUser
from decimal import Decimal, InvalidOperation
from django.utils.timezone import now
from django.utils import timezone
from django.conf import settings
from main.views.courses import user_can_manage_tutor_admin
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
            "tutor_id": s.created_by_id,
            "when": s.starts_at.isoformat(),
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
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)

    if request.method == "GET":
        qs = ClassSession.objects.select_related('course').filter(created_by=request.user).order_by('starts_at')
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
            "price": str(s.price) if s.price is not None else None,
            "language": s.language,
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
    language = (payload.get('language') or '').strip()
    if language and language not in (request.user.languages or []):
        return JsonResponse({"error": "Choose one of your registered teaching languages"}, status=400)
    raw_price = payload.get('price')
    try:
        price = Decimal(str(raw_price)) if raw_price not in (None, '') else None
        if price is not None and price < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        return JsonResponse({"error": "price must be zero or a positive amount"}, status=400)
    if price == 0:
        price = None
    s = ClassSession.objects.create(course=course, title=title, starts_at=sdt, ends_at=edt, location=loc, capacity=cap, description=desc, created_by=request.user, price=price, language=language)
    return JsonResponse({"id": s.id})


@require_http_methods(["DELETE"]) 
@login_required
def api_tutor_class_detail(request, pk: int):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    s = get_object_or_404(ClassSession, pk=pk, created_by=request.user)
    s.delete()
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
@login_required
def api_tutor_payment_requests(request):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    qs = Reservation.objects.select_related("user", "session").filter(
        session__created_by=request.user, session__price__gt=0
    ).order_by("-created_at")
    return JsonResponse({"results": [{
        "id": r.id, "student": r.user.display_name or r.user.username,
        "student_id": r.user_id, "class_title": r.session.title,
        "price": str(r.session.price), "payment_status": r.payment_status,
    } for r in qs[:200]]})


@require_http_methods(["PATCH"])
@login_required
def api_tutor_payment_request_detail(request, pk):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    reservation = get_object_or_404(Reservation, pk=pk, session__created_by=request.user, session__price__gt=0)
    try:
        status = json.loads(request.body.decode("utf-8")).get("payment_status")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if status not in {"approved", "rejected", "pending"}:
        return JsonResponse({"error": "Invalid payment status"}, status=400)
    was_approved = reservation.payment_status == "approved"
    reservation.payment_status = status
    reservation.save(update_fields=["payment_status", "updated_at"])
    notified = False
    if status == "approved" and not was_approved:
        system_user, created = CustomUser.objects.get_or_create(
            username="stem-lms-system",
            defaults={"display_name": "STEM LMS System", "is_active": False},
        )
        if created:
            system_user.set_unusable_password()
            system_user.save(update_fields=["password"])
        Message.objects.create(
            sender=system_user,
            recipient=reservation.user,
            subject=f"Payment received — {reservation.session.title}",
            body=(
                f"Payment received. Your payment of R{reservation.session.price:.2f} "
                f"for {reservation.session.title} has been verified. Your class access is now released.\n\n"
                f"Class link: {reservation.session.location or 'The tutor will add the class link shortly.'}"
            ),
            related_course=reservation.session.course,
            related_session=reservation.session,
        )
        from main.utils.mail import send_class_payment_received_email
        notified = send_class_payment_received_email(reservation)
    return JsonResponse({"ok": True, "payment_status": status, "notification_sent": notified})
