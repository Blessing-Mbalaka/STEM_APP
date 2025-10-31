from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from ..models import Game, GameQuestion, GameScore
from django.db.models import Max
import json

from main.utils.roles import user_has_role, ROLE_ADMIN

def games(request):
    return render(request, "Games.html")

@login_required
def add_question(request):
    return render(request, "AddQuestion.html")

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

@require_http_methods(["GET", "PATCH", "PUT"])
def api_game_detail(request, pk: int):
    """
    GET /api/games/<id>/ : returns full playable quiz with questions (active only)
    PATCH/PUT /api/games/<id>/ : update basic game fields (active or inactive)
    """
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

    qtype = (data.get("qtype") or "").strip()
    question = (data.get("question") or "").strip()
    order = data.get("order")

    allowed_types = {
        "multiple-choice", "true-false", "fill-blank", "matching", "essay",
        "case-study", "calculation",
        "chart-radar", "chart-pie", "chart-line", "chart-bar", "chart-doughnut", "chart-polar",
    }
    if qtype not in allowed_types:
        return JsonResponse({"error": f"Invalid qtype '{qtype}'"}, status=400)
    if not question:
        return JsonResponse({"error": "question is required"}, status=400)

    if not isinstance(order, int) or order <= 0:
        last = g.questions.aggregate(m=Max("order")).get("m") or 0
        order = last + 1

    fields = {
        "game": g,
        "order": order,
        "qtype": qtype,
        "question": question,
    }

    # Conditional fields by type
    if qtype in {"multiple-choice", "case-study"}:
        options = data.get("options")
        correct_answer = data.get("correct_answer")
        if not isinstance(options, list) or not all(isinstance(x, str) for x in options):
            return JsonResponse({"error": "options must be a list of strings"}, status=400)
        if not isinstance(correct_answer, int) or not (0 <= correct_answer < len(options)):
            return JsonResponse({"error": "correct_answer must be a valid option index"}, status=400)
        fields.update({"options": options, "correct_answer": correct_answer})

    elif qtype == "true-false":
        ca = data.get("correct_answer")
        if not isinstance(ca, bool):
            return JsonResponse({"error": "correct_answer must be true/false"}, status=400)
        fields.update({"correct_answer": ca})

    elif qtype in {"fill-blank", "calculation"}:
        ca = data.get("correct_answer")
        if ca is None:
            return JsonResponse({"error": "correct_answer is required"}, status=400)
        fields.update({"correct_answer": ca})

    elif qtype == "matching":
        left_items = data.get("left_items") or data.get("leftItems")
        right_items = data.get("right_items") or data.get("rightItems")
        correct_matches = data.get("correct_matches") or data.get("correctMatches")
        if not isinstance(left_items, list) or not all(isinstance(x, str) for x in left_items):
            return JsonResponse({"error": "left_items must be a list of strings"}, status=400)
        if not isinstance(right_items, list) or not all(isinstance(x, str) for x in right_items):
            return JsonResponse({"error": "right_items must be a list of strings"}, status=400)
        if not isinstance(correct_matches, list) or not all(isinstance(p, (list, tuple)) and len(p) == 2 for p in correct_matches):
            return JsonResponse({"error": "correct_matches must be list of [left_idx,right_idx]"}, status=400)
        fields.update({
            "left_items": left_items,
            "right_items": right_items,
            "correct_matches": [[int(p[0]), int(p[1])] for p in correct_matches],
        })

    elif qtype == "essay":
        min_words = data.get("min_words") or data.get("minWords") or 0
        try:
            min_words = int(min_words)
        except Exception:
            min_words = 0
        fields.update({"min_words": min_words})

    elif qtype.startswith("chart-"):
        chart_data = data.get("chart_data") or data.get("chartData")
        correct_answer = data.get("correct_answer")
        if not isinstance(chart_data, dict):
            return JsonResponse({"error": "chart_data must be an object with labels/datasets"}, status=400)
        if not isinstance(correct_answer, int):
            return JsonResponse({"error": "correct_answer must be an integer index"}, status=400)
        fields.update({"chart_data": chart_data, "correct_answer": correct_answer})

    # Create the question
    q = GameQuestion.objects.create(**fields)
    return JsonResponse(_question_to_dict(q), status=201)
