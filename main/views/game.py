from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from ..models import Game, GameQuestion, GameScore
import json

def games(request):
    return render(request, "Games.html")

# ---------- API: LIST ----------
def api_games_list(request):
    """
    GET filters: ?q=&category=&difficulty=&active=true/false
    Returns a lightweight list for the dashboard.
    """
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
    if active in {"true","false"}:
        qs = qs.filter(is_active=(active == "true"))

    data = [{
        "id": g.id,
        "title": g.title,
        "category": g.category,
        "difficulty": g.difficulty,
        "duration": g.duration_minutes,
        "points": g.max_points,
        "slug": g.slug,
        "is_active": g.is_active,
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

def api_game_detail(request, pk: int):
    """
    GET /api/games/<id> : returns full playable quiz with questions
    """
    g = get_object_or_404(Game, pk=pk, is_active=True)
    questions = [ _question_to_dict(q) for q in g.questions.all() ]
    payload = {
        "id": g.id,
        "title": g.title,
        "category": g.category,
        "difficulty": g.difficulty,
        "duration": g.duration_minutes,
        "points": g.max_points,
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
        points = max(1, calc)

    GameScore.objects.create(
        user=request.user,
        game=g,
        score_percent=score,
        points_awarded=points,
        raw_answers=answers,
    )

    return JsonResponse({"score": score, "points": points})
