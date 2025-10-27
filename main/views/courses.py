# main/views/courses.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.db import transaction
from django.db.models import Max, Q
from django.conf import settings

from main.utils.analytics import collect_dashboard_metrics

def user_can_manage_tutor_admin(user):
    """Return True when the user should access tutor/admin tooling."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    group_name = getattr(settings, "ADMINISTRATOR_GROUP_NAME", "Administrator")
    in_admin_group = False
    if group_name:
        try:
            in_admin_group = user.groups.filter(name__iexact=group_name).exists()
        except Exception:
            in_admin_group = False
    require_staff = getattr(settings, "TUTOR_ADMIN_REQUIRE_STAFF", True)
    require_tutor = getattr(settings, "TUTOR_ADMIN_REQUIRE_TUTOR", False)
    if require_staff:
        if getattr(user, "is_staff", False) or in_admin_group:
            return True
        return False
    if getattr(user, "is_staff", False):
        return True
    if require_tutor and getattr(user, "is_tutor", False):
        return True
    return in_admin_group

def courses(request):
    return render(request, "Courses.html")

@require_GET
def api_courses(request):
    """
    Minimal JSON for Courses page.
    Shape matches the frontend expectation:
    {
      "subjects": {
        "math": { "name": "...", "visual":[{title,duration}], "auditory":[...], "readwrite":[{title,author,pages}] },
        ...
      }
    }
    """
    from main.models.course import Course, CourseResource
    subjects = {}
    for course in Course.objects.filter(is_active=True):
        key = f"course-{course.id}"
        subjects[key] = {
            "name": course.title,
            "classification": (course.classification or '').lower(),
            "visual": [],
            "auditory": [],
            "readwrite": []
        }
        resources = CourseResource.objects.filter(course=course)
        for res in resources:
            entry = {
                "title": res.title,
                "description": res.description,
                "resource_type": res.resource_type,
                "url": res.url,
                "file": res.file.url if res.file else None
            }
            # Add extra fields for read/write
            if res.learning_style == "readwrite":
                entry["author"] = res.description or ""
                entry["pages"] = ""
            if res.learning_style == "visual":
                entry["duration"] = ""
            if res.learning_style == "auditory":
                entry["duration"] = ""
            subjects[key][res.learning_style].append(entry)
    return JsonResponse({"subjects": subjects})


# ---------- Tutor Admin (page) ----------
@login_required
def tutor_admin(request):
    if not user_can_manage_tutor_admin(request.user):
        return HttpResponseForbidden("Forbidden")
    analytics = collect_dashboard_metrics()
    return render(request, "TutorAdmin.html", {"analytics": analytics})


# ---------- Tutor Admin APIs ----------
@require_http_methods(["GET", "POST"])
@login_required
def api_tutor_courses(request):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.course import Course, CourseResource
    if request.method == "GET":
        data = []
        # Show all courses for Tutor Admin. The optional 'mine=true' narrows to just my drafts.
        qs = Course.objects.all().order_by("-created_at")
        mine = (request.GET.get("mine") or "").strip().lower() == 'true'
        if mine and request.user.is_authenticated:
            qs = qs.filter(created_by=request.user)
        for c in qs:
            resources = [{
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "resource_type": r.resource_type,
                "url": r.url,
                "file": (request.build_absolute_uri(r.file.url) if r.file else None),
                "learning_style": r.learning_style,
                "game_id": r.game_id,
                "position": r.position,
                "poll_question": r.poll_question,
                "poll_options": r.poll_options,
                "poll_multi": r.poll_multi,
                "created_at": r.created_at.isoformat(),
            } for r in c.resources.all().order_by("position", "created_at", "id")]
            data.append({
                "id": c.id,
                "title": c.title,
                "summary": c.summary,
                "description": c.description,
                "subject": c.subject,
                "level": c.level,
                "thumbnail": (request.build_absolute_uri(c.thumbnail.url) if c.thumbnail else None),
                "is_active": c.is_active,
                "resources": resources,
                "classification": getattr(c, 'classification', '') or '',
            })
        return JsonResponse({"results": data})

    # POST create course (JSON only for simplicity)
    import json
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    from main.models.course import LEVEL, Course
    title = (payload.get("title") or "").strip()
    if not title:
        return JsonResponse({"error": "title is required"}, status=400)
    # Enforce approval workflow: only staff can create active courses
    # Normalize subject to allowed set
    _subject = (payload.get("subject") or "").strip()
    _class_raw = (payload.get("classification") or "").strip().lower()
    _CLASS = _class_raw if _class_raw in {"stem","steam","general",""} else ""

    c = Course.objects.create(
        title=title,
        summary=payload.get("summary") or "",
        description=payload.get("description") or "",
        subject=_subject,
        classification=_CLASS,
        level=(payload.get("level") or "").strip() if (payload.get("level") or "") in dict(LEVEL) else "",
        is_active=(bool(payload.get("is_active")) if request.user.is_staff else False),
        created_by=request.user if request.user.is_authenticated else None,
    )
    return JsonResponse({"id": c.id, "title": c.title})


@require_http_methods(["PATCH"])
@login_required
def api_tutor_course_detail(request, pk: int):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    import json
    from main.models.course import Course
    c = get_object_or_404(Course, pk=pk)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    changed = False
    for f in ["title", "summary", "description", "subject", "level", "classification", "is_active"]:
        if f in payload:
            if f == "is_active" and not request.user.is_staff:
                # Only staff may toggle activation; enforce False for non-staff updates
                c.is_active = False
            elif f == "classification":
                _raw = (payload.get("classification") or "").strip().lower()
                if _raw in {"stem","steam","general",""}:
                    c.classification = _raw
            else:
                setattr(c, f, payload.get(f))
            changed = True
    if changed:
        c.save()
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
@login_required
@csrf_exempt  # we'll manually check CSRF token from header for multipart
def api_tutor_course_add_resource(request, pk: int):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.course import Course, CourseResource
    c = get_object_or_404(Course, pk=pk)

    # Support multipart (file upload) or JSON
    # compute next position
    from main.models.course import CourseResource
    next_pos = (c.resources.aggregate(m=Max('position')).get('m') or 0) + 1

    if request.content_type and request.content_type.startswith("multipart/"):
        title = (request.POST.get("title") or "").strip()
        if not title:
            return JsonResponse({"error": "title is required"}, status=400)
        r = CourseResource.objects.create(
            course=c,
            title=title,
            description=request.POST.get("description") or "",
            resource_type=request.POST.get("resource_type") or "",
            url=request.POST.get("url") or "",
            learning_style=request.POST.get("learning_style") or "visual",
            file=request.FILES.get("file"),
            position=next_pos,
        )
        if r.resource_type == 'quiz':
            try:
                r.game_id = int(request.POST.get('game_id') or 0) or None
            except Exception:
                r.game_id = None
            r.save()
        if r.resource_type == 'poll':
            r.poll_question = (request.POST.get('poll_question') or '').strip()
            # options as JSON string or multiple fields 'option'
            import json as _json
            opts_raw = request.POST.get('poll_options')
            if opts_raw:
                try:
                    opts = _json.loads(opts_raw)
                except Exception:
                    return JsonResponse({"error": "poll_options must be JSON list"}, status=400)
            else:
                opts = [o for o in request.POST.getlist('option') if o]
            if not isinstance(opts, list) or not all(isinstance(x, str) and x.strip() for x in opts):
                return JsonResponse({"error": "poll_options must be list[str]"}, status=400)
            r.poll_options = opts
            r.poll_multi = (str(request.POST.get('poll_multi') or '').lower() in {'1','true','yes','on'})
            r.save()
        return JsonResponse({"id": r.id})
    else:
        import json
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        title = (payload.get("title") or "").strip()
        if not title:
            return JsonResponse({"error": "title is required"}, status=400)
        r = CourseResource.objects.create(
            course=c,
            title=title,
            description=payload.get("description") or "",
            resource_type=payload.get("resource_type") or "",
            url=payload.get("url") or "",
            learning_style=payload.get("learning_style") or "visual",
            position=next_pos,
        )
        if r.resource_type == 'quiz':
            try:
                r.game_id = int(payload.get('game_id') or 0) or None
            except Exception:
                r.game_id = None
            r.save()
        if r.resource_type == 'poll':
            opts = payload.get('poll_options') or []
            if not isinstance(opts, list) or not all(isinstance(x, str) and x.strip() for x in opts):
                return JsonResponse({"error": "poll_options must be list[str]"}, status=400)
            r.poll_question = (payload.get('poll_question') or '').strip()
            r.poll_options = opts
            r.poll_multi = bool(payload.get('poll_multi'))
            r.save()
        return JsonResponse({"id": r.id})


@require_http_methods(["DELETE"])
@login_required
def api_tutor_resource_detail(request, res_id: int):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.course import CourseResource
    r = get_object_or_404(CourseResource, pk=res_id)
    try:
        # delete associated file
        if r.file:
            r.file.delete(save=False)
    except Exception:
        pass
    r.delete()
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def api_tutor_course_thumbnail(request, pk: int):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    from main.models.course import Course
    c = get_object_or_404(Course, pk=pk)
    f = request.FILES.get('thumbnail')
    if not f:
        return JsonResponse({"error": "No file"}, status=400)
    try:
        if c.thumbnail:
            c.thumbnail.delete(save=False)
    except Exception:
        pass
    c.thumbnail = f
    c.save()
    return JsonResponse({"ok": True, "thumbnail": (request.build_absolute_uri(c.thumbnail.url) if c.thumbnail else None)})


@require_http_methods(["POST"])
@login_required
def api_tutor_course_reorder(request, pk: int):
    if not user_can_manage_tutor_admin(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    import json
    from main.models.course import Course, CourseResource
    c = get_object_or_404(Course, pk=pk)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    order = payload.get('order')
    if not isinstance(order, list) or not all(isinstance(x, int) for x in order):
        return JsonResponse({"error": "order must be list[int]"}, status=400)
    # Ensure all belong to this course
    ids = set(order)
    res_qs = c.resources.filter(id__in=ids)
    if res_qs.count() != len(ids):
        return JsonResponse({"error": "Some resources not found for this course"}, status=400)
    with transaction.atomic():
        for pos, rid in enumerate(order, start=1):
            CourseResource.objects.filter(pk=rid, course=c).update(position=pos)
    return JsonResponse({"ok": True})


# ---------- Student sequence + poll vote ----------
@require_http_methods(["GET"])
@login_required
def api_course_sequence(request, pk: int):
    from main.models.course import Course
    c = get_object_or_404(Course, pk=pk, is_active=True)
    data = []
    for r in c.resources.all():
        item = {
            "id": r.id,
            "type": r.resource_type,
            "title": r.title,
            "description": r.description,
            "url": r.url,
            "file": (request.build_absolute_uri(r.file.url) if r.file else None),
            "learning_style": r.learning_style,
        }
        if r.resource_type == 'quiz' and r.game_id:
            item["game_id"] = r.game_id
        if r.resource_type == 'poll':
            item["question"] = r.poll_question
            item["options"] = r.poll_options or []
            # include my vote if any
            v = r.votes.filter(user=request.user).first()
            item["my_vote"] = v.choices if v else None
            # results summary
            total = max(1, r.votes.count())
            counts = [0] * len(item["options"])
            for vv in r.votes.all():
                try:
                    for idx in vv.choices:
                        counts[int(idx)] += 1
                except Exception:
                    pass
            item["results"] = counts
            item["multi"] = bool(r.poll_multi)
        data.append(item)
    return JsonResponse({"course": {"id": c.id, "title": c.title}, "sequence": data})


@require_http_methods(["POST"])
@login_required
def api_course_poll_vote(request, pk: int, res_id: int):
    import json
    from main.models.course import Course, CourseResource
    from main.models.poll import CoursePollVote
    c = get_object_or_404(Course, pk=pk, is_active=True)
    r = get_object_or_404(CourseResource, pk=res_id, course=c, resource_type='poll')
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    choices = payload.get('choices')
    if r.poll_multi:
        if not isinstance(choices, list) or not all(isinstance(x, int) for x in choices):
            return JsonResponse({"error": "choices must be list[int]"}, status=400)
    else:
        if not isinstance(choices, int):
            return JsonResponse({"error": "choices must be int"}, status=400)
        choices = [choices]
    # bounds
    if not all(0 <= int(i) < len(r.poll_options or []) for i in choices):
        return JsonResponse({"error": "choice out of range"}, status=400)
    vote, _ = CoursePollVote.objects.update_or_create(user=request.user, resource=r, defaults={"choices": choices})
    return JsonResponse({"ok": True})
