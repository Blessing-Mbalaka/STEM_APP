from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import models
from main.models import Message, CustomUser, Course, ClassSession
import json

@login_required
def messages_page(request):
    return render(request, "Messages.html")


@require_http_methods(["GET"])
@login_required
def api_messages_list(request):
    unread = request.GET.get("unread")
    box = (request.GET.get("box") or "inbox").strip().lower()  # inbox|sent
    q = (request.GET.get("q") or "").strip()
    if box == "sent":
        qs = Message.objects.filter(sender=request.user)
    else:
        qs = Message.objects.filter(recipient=request.user)
    if unread in {"1", "true", "yes"}:
        qs = qs.filter(read_at__isnull=True)
    if q:
        qs = qs.filter(Q(subject__icontains=q) | Q(body__icontains=q))
    qs = qs.select_related("sender", "related_course", "related_session").order_by("-created_at")[:100]
    data = [{
        "id": m.id,
        "sender_id": m.sender_id,
        "from": m.sender.display_name or m.sender.username,
        "subject": m.subject,
        "body": m.body,
        "read": bool(m.read_at),
        "created_at": m.created_at.isoformat(),
        "course": m.related_course.title if m.related_course_id else None,
        "session_id": m.related_session_id,
    } for m in qs]
    return JsonResponse({"results": data})


@require_http_methods(["GET"])
@login_required
def api_messages_recipients(request):
    """Return a simple list of tutors/staff that can receive messages."""
    users = CustomUser.objects.filter(is_active=True).filter(models.Q(is_tutor=True) | models.Q(is_staff=True)).order_by('username')
    data = [{
        "id": u.id,
        "name": (getattr(u, 'display_name', '') or '').strip() or (f"{getattr(u,'first_name','')} {getattr(u,'last_name','')}".strip()) or u.username,
    } for u in users[:200]]
    return JsonResponse({"results": data})


@require_http_methods(["POST"])
@login_required
def api_messages_create(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    try:
        recipient_id = int(payload.get("recipient_id"))
    except Exception:
        return JsonResponse({"error": "recipient_id required"}, status=400)

    recipient = get_object_or_404(CustomUser, pk=recipient_id)
    subject = (payload.get("subject") or "").strip()
    body = (payload.get("body") or "").strip()
    if not body:
        return JsonResponse({"error": "body required"}, status=400)
    related_course = None
    related_session = None
    try:
        if payload.get("related_course"):
            related_course = Course.objects.get(pk=int(payload.get("related_course")))
    except Exception:
        related_course = None
    try:
        if payload.get("related_session"):
            related_session = ClassSession.objects.get(pk=int(payload.get("related_session")))
    except Exception:
        related_session = None

    m = Message.objects.create(
        sender=request.user,
        recipient=recipient,
        subject=subject,
        body=body,
        related_course=related_course,
        related_session=related_session,
    )
    return JsonResponse({"id": m.id})


@require_http_methods(["PATCH"])
@login_required
def api_messages_read(request, pk: int):
    m = get_object_or_404(Message, pk=pk, recipient=request.user)
    if not m.read_at:
        m.read_at = timezone.now()
        m.save(update_fields=["read_at"])
    return JsonResponse({"ok": True})
