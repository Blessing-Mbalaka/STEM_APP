from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from ..models import Game, GameQuestion, GameScore
from django.db.models import Max, F
from django.core.serializers.json import DjangoJSONEncoder
import json

from main.utils.roles import user_has_role, ROLE_ADMIN

def games(request):
    return render(request, "Games.html")

@login_required
def add_question(request):
    games = [
        {
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "category": g.category,
            "difficulty": g.difficulty,
            "duration": g.duration_minutes,
            "points": g.max_points,
            "is_active": g.is_active,
            "question_count": g.questions.count(),
            "created_by": getattr(g.created_by, "id", None),
        }
        for g in Game.objects.all().order_by("title")
    ]
    context = {
        "quiz_bootstrap": json.dumps(games, cls=DjangoJSONEncoder),
    }
    return render(request, "AddQuestion.html", context)

# ---------- API: LIST ----------
@require_http_methods(["GET", "POST"])
def api_games_list(request):
    """
    GET filters: ?q=&category=&difficulty=&active=true/false
    Returns a lightweight list for the dashboard.

    POST body:
    { title, description?, category?, difficulty?, duration_minutes?, max_points?, is_active? }
    Creates a Game and returns its summary.
    """
    if request.method == "POST":
        # Only authenticated users may create games; non-staff creations are inactive until admin approval
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=401)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        title = (data.get("title") or "").strip()
        if not title:
            return JsonResponse({"error": "title is required"}, status=400)
        description = data.get("description") or ""
        category = (data.get("category") or "").strip().lower()
        if category not in {"stem","steam","general",""}:
            category = "general" if category else ""
        difficulty = (data.get("difficulty") or "").strip().lower()
        if difficulty not in {"easy", "medium", "hard", ""}:
            difficulty = ""
        try:
            duration_minutes = int(data.get("duration_minutes") or data.get("duration") or 15)
        except Exception:
            duration_minutes = 15
        try:
            max_points = int(data.get("max_points") or data.get("points") or 10)
        except Exception:
            max_points = 10
        # Enforce approval workflow: only staff can control activation
        is_active = bool(data.get("is_active")) if user_has_role(request.user, ROLE_ADMIN) else False

        g = Game.objects.create(
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            duration_minutes=duration_minutes,
            max_points=max_points,
            is_active=is_active,
            created_by=request.user,
        )
        resp = {
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "category": g.category,
            "difficulty": g.difficulty,
            "duration": g.duration_minutes,
            "points": g.max_points,
            "slug": g.slug,
            "is_active": g.is_active,
            "question_count": g.questions.count(),
        }
        return JsonResponse(resp, status=201)

    qs = Game.objects.all().order_by("-created_at")
    q = (request.GET.get("q") or "").strip()
    category = (request.GET.get("category") or "").strip()
    difficulty = (request.GET.get("difficulty") or "").strip()
    active = (request.GET.get("active") or "").strip().lower()

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category:
        qs = qs.filter(category__iexact=category)
    if difficulty:
        qs = qs.filter(difficulty__iexact=difficulty)
    mine = (request.GET.get("mine") or "").strip().lower() == 'true'
    # Only staff may view inactive entries in general; allow tutors to view their own drafts with ?mine=true
    if request.user.is_authenticated and user_has_role(request.user, ROLE_ADMIN):
        if active in {"true","false"}:
            qs = qs.filter(is_active=(active == "true"))
        if mine:
            qs = qs.filter(created_by=request.user)
    else:
        if mine and request.user.is_authenticated:
            qs = qs.filter(created_by=request.user)
        else:
            qs = qs.filter(is_active=True)

    data = [{
        "id": g.id,
        "title": g.title,
        "description": g.description,
        "category": g.category,
        "difficulty": g.difficulty,
        "duration": g.duration_minutes,
        "points": g.max_points,
        "slug": g.slug,
        "is_active": g.is_active,
        "question_count": g.questions.count(),
    } for g in qs]
    return JsonResponse({"results": data})


# ---------- API: DETAIL ----------
def _question_to_dict(q: GameQuestion):
    base = {
        "id": q.order,
        "order": q.order,
        "type": q.qtype,
        "question": q.question,
    }
    # MC-like
    if q.qtype in {"multiple-choice","case-study"}:
        base["options"] = q.options or []
    # TF
    if q.qtype == "true-false":
        # front-end expects buttons; nothing else needed
        pass
    # matching
    if q.qtype == "matching":
        base["leftItems"] = q.left_items or []
        base["rightItems"] = q.right_items or []
    # essay
    if q.qtype == "essay":
        base["minWords"] = q.min_words or 0
    # fill/calculation
    if q.qtype in {"fill-blank","calculation"}:
        # nothing extra
        pass
    # charts
    if q.qtype.startswith("chart-"):
        base["chartData"] = q.chart_data or {"labels": [], "datasets": []}
        # MC-like options use chartData.labels as options
    return base


def _question_admin_dict(q: GameQuestion):
    base = {
        "questionId": q.id,
        "order": q.order,
        "qtype": q.qtype,
        "question": q.question,
    }
    if q.qtype in {"multiple-choice", "case-study"}:
        base["options"] = q.options or []
        base["correctAnswer"] = q.correct_answer
    elif q.qtype == "true-false":
        base["correctAnswer"] = bool(q.correct_answer)
    elif q.qtype in {"fill-blank", "calculation"}:
        base["correctAnswer"] = q.correct_answer
    elif q.qtype == "matching":
        base["leftItems"] = q.left_items or []
        base["rightItems"] = q.right_items or []
        base["correctMatches"] = [
            [int(pair[0]), int(pair[1])]
            for pair in (q.correct_matches or [])
            if isinstance(pair, (list, tuple)) and len(pair) == 2
        ]
    elif q.qtype == "essay":
        base["minWords"] = q.min_words or 0
    elif q.qtype.startswith("chart-"):
        base["chartData"] = q.chart_data or {"labels": [], "datasets": []}
        base["correctAnswer"] = q.correct_answer
    else:
        base["correctAnswer"] = q.correct_answer
    return base


def _parse_question_payload(game: Game, data: dict, existing=None):
    allowed_types = {
        "multiple-choice", "true-false", "fill-blank", "matching", "essay",
        "case-study", "calculation",
        "chart-radar", "chart-pie", "chart-line", "chart-bar", "chart-doughnut", "chart-polar",
    }

    qtype = (data.get("qtype") or (existing.qtype if existing else "")).strip()
    if qtype not in allowed_types:
        raise ValueError(f"Invalid qtype '{qtype}'")

    question_text = (data.get("question") or (existing.question if existing else "")).strip()
    if not question_text:
        raise ValueError("question is required")

    payload: dict[str, object] = {
        "qtype": qtype,
        "question": question_text,
    }

    order = None
    if "order" in data:
        try:
            order = int(data.get("order"))
        except Exception as exc:
            raise ValueError("order must be an integer") from exc
        if order <= 0:
            raise ValueError("order must be greater than zero")
    elif existing:
        order = existing.order

    if qtype in {"multiple-choice", "case-study"}:
        if "options" in data:
            options = data.get("options")
        else:
            options = existing.options if existing else None
        if not isinstance(options, list) or not all(isinstance(opt, str) for opt in options or []):
            raise ValueError("options must be a list of strings")
        if not options:
            raise ValueError("options must include at least one value")
        if "correct_answer" in data:
            correct_answer = data.get("correct_answer")
        elif existing is not None:
            correct_answer = existing.correct_answer
        else:
            correct_answer = None
        if not isinstance(correct_answer, int) or not (0 <= correct_answer < len(options)):
            raise ValueError("correct_answer must be a valid option index")
        payload["options"] = options
        payload["correct_answer"] = correct_answer

    elif qtype == "true-false":
        if "correct_answer" in data:
            correct_answer = data.get("correct_answer")
        elif existing is not None:
            correct_answer = existing.correct_answer
        else:
            correct_answer = None
        if not isinstance(correct_answer, bool):
            raise ValueError("correct_answer must be true or false")
        payload["correct_answer"] = correct_answer

    elif qtype in {"fill-blank", "calculation"}:
        if "correct_answer" in data:
            correct_answer = data.get("correct_answer")
        elif existing is not None:
            correct_answer = existing.correct_answer
        else:
            correct_answer = None
        if correct_answer is None:
            raise ValueError("correct_answer is required")
        payload["correct_answer"] = correct_answer

    elif qtype == "matching":
        if "left_items" in data or "leftItems" in data:
            left_items = data.get("left_items") or data.get("leftItems")
        else:
            left_items = existing.left_items if existing else None
        if "right_items" in data or "rightItems" in data:
            right_items = data.get("right_items") or data.get("rightItems")
        else:
            right_items = existing.right_items if existing else None
        if not isinstance(left_items, list) or not all(isinstance(x, str) for x in left_items or []):
            raise ValueError("left_items must be a list of strings")
        if not isinstance(right_items, list) or not all(isinstance(x, str) for x in right_items or []):
            raise ValueError("right_items must be a list of strings")
        if not left_items or not right_items:
            raise ValueError("left_items and right_items cannot be empty")
        if "correct_matches" in data or "correctMatches" in data:
            raw_matches = data.get("correct_matches") or data.get("correctMatches")
        else:
            raw_matches = existing.correct_matches if existing else None
        if not isinstance(raw_matches, list):
            raise ValueError("correct_matches must be a list of [left_idx, right_idx]")
        matches: list[list[int]] = []
        for pair in raw_matches:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError("correct_matches must contain [left_idx, right_idx] pairs")
            li, ri = int(pair[0]), int(pair[1])
            if not (0 <= li < len(left_items)) or not (0 <= ri < len(right_items)):
                raise ValueError("correct_matches indexes must reference valid options")
            matches.append([li, ri])
        payload["left_items"] = left_items
        payload["right_items"] = right_items
        payload["correct_matches"] = matches

    elif qtype == "essay":
        if "min_words" in data or "minWords" in data:
            min_words = data.get("min_words", data.get("minWords"))
        elif existing is not None:
            min_words = existing.min_words
        else:
            min_words = 0
        try:
            payload["min_words"] = int(min_words or 0)
        except Exception as exc:
            raise ValueError("min_words must be an integer") from exc

    elif qtype.startswith("chart-"):
        if "chart_data" in data or "chartData" in data:
            chart_data = data.get("chart_data") or data.get("chartData")
        else:
            chart_data = existing.chart_data if existing else None
        if not isinstance(chart_data, dict):
            raise ValueError("chart_data must be an object with labels/datasets")
        labels = chart_data.get("labels") or []
        if not isinstance(labels, list) or not all(isinstance(x, str) for x in labels):
            raise ValueError("chart_data.labels must be a list of strings")
        datasets = chart_data.get("datasets") or []
        if not isinstance(datasets, list):
            raise ValueError("chart_data.datasets must be a list")
        if "correct_answer" in data:
            correct_answer = data.get("correct_answer")
        elif existing is not None:
            correct_answer = existing.correct_answer
        else:
            correct_answer = None
        if not isinstance(correct_answer, int):
            raise ValueError("correct_answer must be an integer index")
        payload["chart_data"] = {"labels": labels, "datasets": datasets}
        payload["correct_answer"] = correct_answer

    return payload, order

@require_http_methods(["GET", "PATCH", "PUT", "DELETE"])
def api_game_detail(request, pk: int):
    """
    GET /api/games/<id>/ : returns full playable quiz with questions (active only)
    PATCH/PUT /api/games/<id>/ : update basic game fields (active or inactive)
    """
    if request.method == "DELETE":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=401)
        g = get_object_or_404(Game, pk=pk)
        allowed = user_has_role(request.user, ROLE_ADMIN) or g.created_by_id == getattr(request.user, "id", None)
        if not allowed:
            return JsonResponse({"error": "Not allowed"}, status=403)
        g.delete()
        return JsonResponse({"status": "deleted"})

    if request.method in {"PATCH", "PUT"}:
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=401)
        g = get_object_or_404(Game, pk=pk)

        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        changed = False
        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                return JsonResponse({"error": "title cannot be empty"}, status=400)
            g.title = title; changed = True
        if "description" in data:
            g.description = data.get("description") or ""; changed = True
        if "category" in data:
            cat = (data.get("category") or "").strip().lower()
            if cat not in {"stem","steam","general",""}:
                return JsonResponse({"error": "category must be stem, steam, general or empty"}, status=400)
            g.category = cat; changed = True
        if "difficulty" in data:
            diff = (data.get("difficulty") or "").strip().lower()
            if diff not in {"easy","medium","hard",""}:
                return JsonResponse({"error": "difficulty must be easy, medium, hard or empty"}, status=400)
            g.difficulty = diff; changed = True
        if "duration_minutes" in data or "duration" in data:
            try:
                g.duration_minutes = int(data.get("duration_minutes") if "duration_minutes" in data else data.get("duration"))
            except Exception:
                return JsonResponse({"error": "duration_minutes must be an integer"}, status=400)
            changed = True
        if "max_points" in data or "points" in data:
            try:
                g.max_points = int(data.get("max_points") if "max_points" in data else data.get("points"))
            except Exception:
                return JsonResponse({"error": "max_points must be an integer"}, status=400)
            changed = True
        if "is_active" in data:
            # Only staff can change activation state
            if user_has_role(request.user, ROLE_ADMIN):
                g.is_active = bool(data.get("is_active")); changed = True

        if changed:
            g.save()

        resp = {
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "category": g.category,
            "difficulty": g.difficulty,
            "duration": g.duration_minutes,
            "points": g.max_points,
            "slug": g.slug,
            "is_active": g.is_active,
            "question_count": g.questions.count(),
        }
        return JsonResponse(resp)

    # GET path: only active games should be playable
    g = get_object_or_404(Game, pk=pk, is_active=True)
    questions = [ _question_to_dict(q) for q in g.questions.all() ]
    payload = {
        "id": g.id,
        "title": g.title,
        "description": g.description,
        "category": g.category,
        "difficulty": g.difficulty,
        "duration": g.duration_minutes,
        "points": g.max_points,
        "is_active": g.is_active,
        "questions": questions,
    }
    return JsonResponse(payload)


# ---------- API: SUBMIT ----------
@require_http_methods(["POST"])
@login_required
def api_game_submit(request, pk: int):
    """
    POST /api/games/<id>/submit
    Body: {"answers": [...]}  // same length/order as questions (by 'order')
    Returns: {"score": 0-100, "points": int}
    """
    g = get_object_or_404(Game, pk=pk, is_active=True)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    answers = data.get("answers")
    if not isinstance(answers, list):
        return JsonResponse({"error": "answers must be a list"}, status=400)

    # Build question list in order
    qs = list(g.questions.all())
    if len(answers) != len(qs):
        return JsonResponse({"error": "answers length mismatch"}, status=400)

    correct = 0
    answered = 0

    for idx, q in enumerate(qs):
        a = answers[idx]
        # count "answered"
        if a is not None and a != "":
            answered += 1

        qtype = q.qtype
        ca = q.correct_answer

        try:
            if qtype in {"multiple-choice","case-study"}:
                # expect integer index
                if isinstance(a, int) and isinstance(ca, int) and a == ca:
                    correct += 1

            elif qtype == "true-false":
                # expect true/false
                if isinstance(a, bool) and isinstance(ca, bool) and a == ca:
                    correct += 1

            elif qtype in {"fill-blank","calculation"}:
                # compare lowercase strings trimmed
                if isinstance(a, (str,int,float)) and isinstance(ca, (str,int,float)):
                    av = str(a).strip().lower()
                    cv = str(ca).strip().lower()
                    if av == cv:
                        correct += 1

            elif qtype == "matching":
                # expect list of [left_idx, right_idx]
                if isinstance(a, list) and isinstance(q.correct_matches, list):
                    # All correct pairs present and counts equal
                    user_set = { (int(p[0]), int(p[1])) for p in a if isinstance(p, (list,tuple)) and len(p)==2 }
                    corr_set = { (int(p[0]), int(p[1])) for p in q.correct_matches }
                    if user_set == corr_set:
                        correct += 1

            elif qtype == "essay":
                # basic: count as correct if non-empty and passes min_words
                minw = q.min_words or 0
                if isinstance(a, str):
                    words = len([w for w in a.strip().split() if w])
                    if words >= minw:
                        correct += 1

            elif qtype.startswith("chart-"):
                # treated as multiple-choice: pick index corresponding to chartData.labels
                if isinstance(a, int) and isinstance(ca, int) and a == ca:
                    correct += 1
        except Exception:
            # If one question explodes, we just treat it as incorrect rather than 500
            pass

    total = len(qs) if qs else 1
    score = round((correct / total) * 100)

    # Points: proportional to score; minimum 1 if answered anything
    points = 0
    if answered > 0:
        calc = round(g.max_points * (score / 100))
        points = calc #0 if score == 0 else max(1, calc)

    GameScore.objects.create(
        user=request.user,
        game=g,
        score_percent=score,
        points_awarded=points,
        raw_answers=answers,
    )

    # Assign badges based on points
    badges = []
    if points >= 50:
        badges.append("Gold Badge")
    elif points >= 30:
        badges.append("Silver Badge")
    elif points >= 10:
        badges.append("Bronze Badge")
    elif answered > 0:
        badges.append("Participation Badge")

    return JsonResponse({"score": score, "points": points})


# ---------- API: ADD QUESTION ----------
@require_http_methods(["POST"])
@login_required
def api_game_add_question(request, pk: int):
    """
    POST /api/games/<id>/questions/
    Body fields vary by qtype; creates a GameQuestion and returns its dict form.
    """
    g = get_object_or_404(Game, pk=pk)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        fields, order = _parse_question_payload(g, data)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    if order is None:
        order = g.questions.aggregate(m=Max("order")).get("m") or 0
        order += 1

    fields.update({
        "game": g,
        "order": order,
    })
    q = GameQuestion.objects.create(**fields)
    return JsonResponse(_question_to_dict(q), status=201)


@require_http_methods(["GET"])
@login_required
def api_game_questions_manage(request, pk: int):
    g = get_object_or_404(Game, pk=pk)
    allowed = user_has_role(request.user, ROLE_ADMIN) or g.created_by_id == getattr(request.user, "id", None)
    if not allowed:
        return JsonResponse({"error": "Forbidden"}, status=403)
    questions = [
        _question_admin_dict(q)
        for q in g.questions.order_by("order", "id")
    ]
    return JsonResponse({"questions": questions})


@require_http_methods(["PATCH", "DELETE"])
@login_required
def api_game_question_manage(request, pk: int, question_id: int):
    g = get_object_or_404(Game, pk=pk)
    allowed = user_has_role(request.user, ROLE_ADMIN) or g.created_by_id == getattr(request.user, "id", None)
    if not allowed:
        return JsonResponse({"error": "Forbidden"}, status=403)

    q = get_object_or_404(GameQuestion, pk=question_id, game=g)

    if request.method == "DELETE":
        removed_order = q.order
        q.delete()
        GameQuestion.objects.filter(game=g, order__gt=removed_order).update(order=F("order") - 1)
        return JsonResponse({"status": "deleted"})

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        fields, desired_order = _parse_question_payload(g, data, existing=q)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    new_order = desired_order if desired_order is not None else q.order
    if new_order <= 0:
        return JsonResponse({"error": "order must be greater than zero"}, status=400)

    if new_order != q.order:
        if new_order < q.order:
            GameQuestion.objects.filter(game=g, order__lt=q.order, order__gte=new_order).update(order=F("order") + 1)
        else:
            GameQuestion.objects.filter(game=g, order__gt=q.order, order__lte=new_order).update(order=F("order") - 1)
        q.order = new_order

    # Reset type-specific fields before applying new data
    q.qtype = fields.pop("qtype")
    q.question = fields.pop("question")
    q.options = None
    q.correct_answer = None
    q.left_items = None
    q.right_items = None
    q.correct_matches = None
    q.min_words = None
    q.chart_data = None

    for key, value in fields.items():
        setattr(q, key, value)

    q.save()
    return JsonResponse(_question_admin_dict(q))
