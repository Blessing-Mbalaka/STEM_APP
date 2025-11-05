from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from ..models import (
    CustomUserSurvey,
    CustomUserSurveyParticipant,
    CustomUserSurveyQuestion,
    CustomUserSurveyResponse,
)
from ..utils.roles import (
    ROLE_ADMIN,
    ROLE_ANONYMOUS,
    ROLE_STUDENT,
    ROLE_TUTOR,
    get_primary_role,
    user_has_role,
)

ChartDataset = Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_body(request) -> Dict[str, Any]:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload") from exc


def _survey_to_dict(
    survey: CustomUserSurvey,
    *,
    include_questions: bool = False,
    include_counts: bool = True,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "id": survey.id,
        "slug": survey.slug,
        "title": survey.title,
        "description": survey.description,
        "introText": survey.intro_text,
        "outroText": survey.outro_text,
        "consentText": survey.consent_text,
        "isActive": survey.is_active,
        "requireConsent": survey.require_consent,
        "targetRoles": survey.target_roles or [],
        "displayRules": survey.display_rules or {},
        "createdAt": survey.created_at.isoformat(),
        "updatedAt": survey.updated_at.isoformat(),
    }
    if survey.created_by_id:
        payload["createdBy"] = survey.created_by_id

    if include_counts or include_questions:
        qs = survey.questions.order_by("order", "id")
        if include_questions:
            payload["questions"] = [_question_to_dict(q) for q in qs]
        payload["questionCount"] = qs.count()

    if include_counts:
        participants = survey.participants.all()
        completed = participants.filter(status="completed").count()
        pending = participants.exclude(status="completed").count()
        payload["participantCounts"] = {
            "total": participants.count(),
            "completed": completed,
            "pending": pending,
        }

    return payload


def _question_to_dict(question: CustomUserSurveyQuestion) -> Dict[str, Any]:
    return {
        "id": question.id,
        "order": question.order,
        "type": question.qtype,
        "prompt": question.prompt,
        "helpText": question.help_text,
        "isRequired": question.is_required,
        "isScored": question.is_scored,
        "maxScore": question.max_score,
        "chartType": question.chart_type,
        "config": question.config or {},
    }


def _participant_to_dict(participant: CustomUserSurveyParticipant) -> Dict[str, Any]:
    return {
        "id": participant.id,
        "surveyId": participant.survey_id,
        "userId": participant.user_id,
        "status": participant.status,
        "consentedAt": participant.consented_at.isoformat() if participant.consented_at else None,
        "dismissedAt": participant.dismissed_at.isoformat() if participant.dismissed_at else None,
        "lastPromptedAt": participant.last_prompted_at.isoformat() if participant.last_prompted_at else None,
    }


def _build_chart_palette(count: int) -> List[str]:
    palette = [
        "#24adb7",
        "#f57c00",
        "#ffd166",
        "#06d6a0",
        "#118ab2",
        "#ef476f",
        "#073b4c",
        "#8ecae6",
        "#ffb703",
        "#219ebc",
    ]
    if count <= len(palette):
        return palette[:count]
    # Extend palette by repeating with alpha variations
    extended = palette[:]
    while len(extended) < count:
        extended.extend(palette)
    return extended[:count]


def _role_allows_survey(user, survey: CustomUserSurvey) -> bool:
    if user_has_role(user, ROLE_ADMIN):
        return True
    role = get_primary_role(user)
    if not survey.is_active:
        return False
    if role == ROLE_ANONYMOUS:
        return False
    allowed_roles = survey.target_roles or []
    return not allowed_roles or role in allowed_roles


def _validate_target_roles(raw_roles: Any) -> List[str]:
    if raw_roles in (None, "", []):
        return []
    if not isinstance(raw_roles, (list, tuple)):
        raise ValueError("target_roles must be a list.")
    roles: List[str] = []
    for role in raw_roles:
        value = str(role or "").strip().lower()
        if not value:
            continue
        roles.append(value)
    return roles


def _ensure_admin(user):
    if not user_has_role(user, ROLE_ADMIN):
        return False
    return True


def _clean_question_config(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    raise ValueError("config must be an object.")


def _ensure_order_gapless(survey: CustomUserSurvey) -> None:
    """
    Normalize question order to 1..n to avoid duplicates after deletions.
    """
    order = 1
    for question in survey.questions.order_by("order", "id"):
        if question.order != order:
            CustomUserSurveyQuestion.objects.filter(pk=question.pk).update(order=order)
        order += 1


def _evaluate_score(
    question: CustomUserSurveyQuestion,
    value: Any,
) -> Tuple[float, float]:
    """
    Returns (score, max_possible_score) for the provided value.
    """
    if not question.is_scored:
        return 0.0, float(question.normalised_max_score())

    max_score = float(question.normalised_max_score())
    score = 0.0

    if question.qtype == "single-choice":
        mapping = question.option_scores()
        score = float(mapping.get(str(value), 0.0))
    elif question.qtype == "multi-choice":
        mapping = question.option_scores()
        items = value if isinstance(value, list) else []
        current = 0.0
        for item in items:
            current += float(mapping.get(str(item), 0.0))
        score = current
    elif question.qtype in {"rating", "number", "scale"}:
        try:
            score = float(value)
        except (TypeError, ValueError):
            score = 0.0
    else:
        # Unsupported type for scoring, fallback to zero.
        score = 0.0

    if max_score > 0:
        score = max(0.0, min(score, max_score))
    return float(score), max_score


def _individual_chart_payload(
    question: CustomUserSurveyQuestion,
    score: float,
    max_score: float,
) -> Optional[Dict[str, Any]]:
    if not question.chart_type or not question.is_scored:
        return None
    chart_type = question.chart_type or "doughnut"
    remaining = max(0.0, max_score - score)
    return {
        "type": chart_type,
        "data": {
            "labels": ["My Score", "Remaining"],
            "datasets": [
                {
                    "label": question.prompt[:60],
                    "data": [round(score, 2), round(remaining, 2)],
                    "backgroundColor": _build_chart_palette(2),
                }
            ],
        },
    }


def _aggregate_question_chart(
    question: CustomUserSurveyQuestion,
    answers: List[Any],
    score_entries: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not answers and not score_entries:
        return None

    chart_type = question.chart_type or ""

    if question.qtype in {"single-choice", "multi-choice"}:
        labels_map = question.option_labels()
        counts: Dict[str, int] = {key: 0 for key in labels_map.keys()}
        for answer in answers:
            if question.qtype == "multi-choice":
                if isinstance(answer, list):
                    for item in answer:
                        key = str(item)
                        if key in counts:
                            counts[key] += 1
            else:
                key = str(answer)
                if key in counts:
                    counts[key] += 1
        labels: List[str] = []
        data: List[int] = []
        for value, label in labels_map.items():
            labels.append(label)
            data.append(counts.get(value, 0))
        if not any(data):
            return None
        dataset = {
            "label": "Responses",
            "data": data,
            "backgroundColor": _build_chart_palette(len(labels)),
        }
        resolved_type = chart_type or "pie"
        return {
            "type": resolved_type,
            "questionId": question.id,
            "prompt": question.prompt,
            "data": {
                "labels": labels,
                "datasets": [dataset],
            },
        }

    # Numeric / scored questions fall back to average score representation
    scores: List[float] = []
    for entry in score_entries:
        if isinstance(entry, dict) and entry.get("id") == question.id:
            try:
                scores.append(float(entry.get("score", 0)))
            except (TypeError, ValueError):
                continue
    if not scores:
        # attempt to coerce numeric values from answers
        for raw in answers:
            try:
                scores.append(float(raw))
            except (TypeError, ValueError):
                continue
    if not scores:
        return None

    avg_score = sum(scores) / max(len(scores), 1)
    dataset = {
        "label": "Average Score",
        "data": [round(avg_score, 2)],
        "backgroundColor": _build_chart_palette(1),
    }
    resolved_type = chart_type or "bar"
    labels = ["Average"]
    max_score = question.normalised_max_score()
    meta = {"average": round(avg_score, 2), "maxScore": max_score}
    return {
        "type": resolved_type,
        "questionId": question.id,
        "prompt": question.prompt,
        "data": {"labels": labels, "datasets": [dataset]},
        "meta": meta,
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


@login_required
def survey_builder(request):
    if not _ensure_admin(request.user):
        return HttpResponseForbidden("Only administrators can access the survey builder.")
    return render(request, "SurveyBuilder.html")


@login_required
@require_http_methods(["GET", "POST"])
def api_surveys_collection(request):
    if request.method == "GET":
        if not _ensure_admin(request.user):
            return JsonResponse({"error": "Forbidden"}, status=403)
        surveys = CustomUserSurvey.objects.all().order_by("-created_at")
        data = [_survey_to_dict(s, include_questions=False) for s in surveys]
        return JsonResponse({"results": data}, status=200)

    # POST
    if not _ensure_admin(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    title = (payload.get("title") or "").strip()
    if not title:
        return JsonResponse({"error": "title is required"}, status=400)

    survey = CustomUserSurvey.objects.create(
        title=title,
        description=payload.get("description", "") or "",
        intro_text=payload.get("introText", "") or "",
        outro_text=payload.get("outroText", "") or "",
        consent_text=payload.get("consentText", "") or "",
        is_active=bool(payload.get("isActive", False)),
        require_consent=bool(payload.get("requireConsent", True)),
        target_roles=_validate_target_roles(payload.get("targetRoles")),
        display_rules=payload.get("displayRules") or {},
        created_by=request.user,
    )

    return JsonResponse(
        {"survey": _survey_to_dict(survey, include_questions=True)},
        status=201,
    )


@login_required
@require_http_methods(["GET", "PATCH", "DELETE"])
def api_survey_detail(request, pk: int):
    survey = get_object_or_404(CustomUserSurvey, pk=pk)

    if request.method == "GET":
        if not _ensure_admin(request.user):
            return JsonResponse({"error": "Forbidden"}, status=403)
        return JsonResponse(
            {"survey": _survey_to_dict(survey, include_questions=True)},
            status=200,
        )

    if not _ensure_admin(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    if request.method == "DELETE":
        survey.delete()
        return JsonResponse({"ok": True}, status=204)

    # PATCH
    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    fields_updated: List[str] = []
    field_map = {
        "title": "title",
        "description": "description",
        "introText": "intro_text",
        "outroText": "outro_text",
        "consentText": "consent_text",
        "requireConsent": "require_consent",
        "displayRules": "display_rules",
    }

    for key, attr in field_map.items():
        if key not in payload:
            continue
        value = payload.get(key)
        if attr == "require_consent":
            survey.require_consent = bool(value)
        elif value is None:
            setattr(survey, attr, "")
        else:
            setattr(survey, attr, value)
        fields_updated.append(attr)

    if "isActive" in payload:
        survey.is_active = bool(payload["isActive"])
        fields_updated.append("is_active")

    if "targetRoles" in payload:
        try:
            survey.target_roles = _validate_target_roles(payload.get("targetRoles"))
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        fields_updated.append("target_roles")

    if fields_updated:
        survey.save(update_fields=fields_updated + ["updated_at"])

    return JsonResponse(
        {"survey": _survey_to_dict(survey, include_questions=True)},
        status=200,
    )


@login_required
@require_http_methods(["GET", "POST"])
def api_survey_questions(request, pk: int):
    survey = get_object_or_404(CustomUserSurvey, pk=pk)
    if not _ensure_admin(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    if request.method == "GET":
        questions = survey.questions.order_by("order", "id")
        return JsonResponse(
            {"questions": [_question_to_dict(q) for q in questions]},
            status=200,
        )

    # POST
    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    qtype = (payload.get("type") or payload.get("qtype") or "").strip()
    if qtype not in dict(CustomUserSurveyQuestion._meta.get_field("qtype").choices):
        return JsonResponse({"error": "Unsupported question type"}, status=400)

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return JsonResponse({"error": "prompt is required"}, status=400)

    help_text = payload.get("helpText") or ""
    is_required = bool(payload.get("isRequired", True))
    is_scored = bool(payload.get("isScored", False))
    max_score = payload.get("maxScore", 0) or 0
    chart_type = (payload.get("chartType") or "").strip()
    order = payload.get("order")
    config = payload.get("config")

    try:
        config_dict = _clean_question_config(config)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    with transaction.atomic():
        total = survey.questions.count()
        desired_order = int(order) if isinstance(order, int) else total + 1
        desired_order = max(1, min(desired_order, total + 1))

        if desired_order <= total:
            CustomUserSurveyQuestion.objects.filter(
                survey=survey,
                order__gte=desired_order,
            ).update(order=F("order") + 1)

        question = CustomUserSurveyQuestion.objects.create(
            survey=survey,
            order=desired_order,
            qtype=qtype,
            prompt=prompt,
            help_text=help_text,
            is_required=is_required,
            is_scored=is_scored,
            max_score=max_score or 0,
            chart_type=chart_type,
            config=config_dict,
        )

    return JsonResponse(
        {"question": _question_to_dict(question)},
        status=201,
    )


@login_required
@require_http_methods(["GET", "PATCH", "DELETE"])
def api_survey_question_detail(request, pk: int, question_id: int):
    survey = get_object_or_404(CustomUserSurvey, pk=pk)
    question = get_object_or_404(CustomUserSurveyQuestion, pk=question_id, survey=survey)

    if not _ensure_admin(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    if request.method == "GET":
        return JsonResponse({"question": _question_to_dict(question)}, status=200)

    if request.method == "DELETE":
        with transaction.atomic():
            order = question.order
            question.delete()
            CustomUserSurveyQuestion.objects.filter(
                survey=survey,
                order__gt=order,
            ).update(order=F("order") - 1)
        return JsonResponse({"ok": True}, status=204)

    # PATCH
    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    updated_fields: List[str] = []
    if "prompt" in payload:
        question.prompt = payload.get("prompt") or ""
        updated_fields.append("prompt")
    if "helpText" in payload:
        question.help_text = payload.get("helpText") or ""
        updated_fields.append("help_text")
    if "isRequired" in payload:
        question.is_required = bool(payload.get("isRequired"))
        updated_fields.append("is_required")
    if "isScored" in payload:
        question.is_scored = bool(payload.get("isScored"))
        updated_fields.append("is_scored")
    if "maxScore" in payload:
        try:
            question.max_score = float(payload.get("maxScore") or 0)
        except (TypeError, ValueError):
            question.max_score = 0
        updated_fields.append("max_score")
    if "chartType" in payload:
        question.chart_type = payload.get("chartType") or ""
        updated_fields.append("chart_type")
    if "config" in payload:
        try:
            question.config = _clean_question_config(payload.get("config"))
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        updated_fields.append("config")
    if "type" in payload or "qtype" in payload:
        qtype = payload.get("type") or payload.get("qtype") or ""
        if qtype not in dict(CustomUserSurveyQuestion._meta.get_field("qtype").choices):
            return JsonResponse({"error": "Unsupported question type"}, status=400)
        question.qtype = qtype
        updated_fields.append("qtype")

    new_order = payload.get("order")
    if isinstance(new_order, int) and new_order != question.order:
        with transaction.atomic():
            total = survey.questions.count()
            desired_order = max(1, min(int(new_order), total))
            if desired_order < question.order:
                CustomUserSurveyQuestion.objects.filter(
                    survey=survey,
                    order__gte=desired_order,
                    order__lt=question.order,
                ).update(order=F("order") + 1)
            elif desired_order > question.order:
                CustomUserSurveyQuestion.objects.filter(
                    survey=survey,
                    order__gt=question.order,
                    order__lte=desired_order,
                ).update(order=F("order") - 1)
            question.order = desired_order
            updated_fields.append("order")

    if updated_fields:
        question.save(update_fields=updated_fields + ["updated_at"])

    return JsonResponse({"question": _question_to_dict(question)}, status=200)


@login_required
@require_http_methods(["GET"])
def api_survey_next(request):
    if user_has_role(request.user, ROLE_ADMIN):
        # Admins are not auto-prompted to avoid interruption.
        return JsonResponse({"survey": None}, status=200)

    role = get_primary_role(request.user)
    if role in (ROLE_ANONYMOUS,):
        return JsonResponse({"survey": None}, status=200)

    now = timezone.now()
    displayable = CustomUserSurvey.objects.filter(is_active=True).order_by("created_at")

    remind_buffer_hours = 24

    for survey in displayable:
        if not survey.allows_role(role):
            continue
        participant, _ = CustomUserSurveyParticipant.objects.get_or_create(
            survey=survey,
            user=request.user,
            defaults={"status": "pending"},
        )

        if participant.status == "completed":
            continue

        rules = survey.display_rules or {}
        try:
            remind_after_hours = int(rules.get("remind_after_hours", remind_buffer_hours))
        except (TypeError, ValueError):
            remind_after_hours = remind_buffer_hours
        remind_after_hours = max(1, remind_after_hours)
        if participant.status == "dismissed" and participant.dismissed_at:
            remind_on = participant.dismissed_at + timedelta(hours=remind_after_hours)
            if remind_on > now:
                continue

        participant.mark_prompted()

        return JsonResponse(
            {
                "survey": _survey_to_dict(survey, include_questions=True, include_counts=False),
                "participant": _participant_to_dict(participant),
            },
            status=200,
        )

    return JsonResponse({"survey": None}, status=200)


@login_required
@require_http_methods(["POST"])
def api_survey_participation(request, pk: int):
    survey = get_object_or_404(CustomUserSurvey, pk=pk)
    if not _role_allows_survey(request.user, survey):
        return JsonResponse({"error": "Forbidden"}, status=403)

    participant, _ = CustomUserSurveyParticipant.objects.get_or_create(
        survey=survey,
        user=request.user,
        defaults={"status": "pending"},
    )

    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    action = str(payload.get("action") or "").strip().lower()
    now = timezone.now()

    if action == "consent":
        participant.status = "consented"
        participant.consented_at = now
        participant.dismissed_at = None
        participant.save(update_fields=["status", "consented_at", "dismissed_at", "updated_at"])
        return JsonResponse(
            {
                "survey": _survey_to_dict(survey, include_questions=True, include_counts=False),
                "participant": _participant_to_dict(participant),
            },
            status=200,
        )

    if action in {"dismiss", "later"}:
        participant.status = "dismissed"
        participant.dismissed_at = now
        participant.save(update_fields=["status", "dismissed_at", "updated_at"])
        return JsonResponse({"participant": _participant_to_dict(participant)}, status=200)

    if action == "decline":
        participant.status = "declined"
        participant.dismissed_at = now
        participant.save(update_fields=["status", "dismissed_at", "updated_at"])
        return JsonResponse({"participant": _participant_to_dict(participant)}, status=200)

    return JsonResponse({"error": "Unsupported action"}, status=400)


@login_required
@require_http_methods(["POST"])
def api_survey_responses(request, pk: int):
    survey = get_object_or_404(CustomUserSurvey, pk=pk)
    if not _role_allows_survey(request.user, survey):
        return JsonResponse({"error": "Forbidden"}, status=403)

    participant, _ = CustomUserSurveyParticipant.objects.get_or_create(
        survey=survey,
        user=request.user,
        defaults={"status": "pending"},
    )

    if participant.status == "completed":
        response = participant.response
        return JsonResponse(
            {
                "participant": _participant_to_dict(participant),
                "survey": _survey_to_dict(survey, include_questions=False),
                "scoreSummary": response.score_summary or {},
            },
            status=200,
        )

    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    answers = payload.get("answers")
    if not isinstance(answers, dict):
        return JsonResponse({"error": "answers must be an object"}, status=400)

    cleaned_answers: Dict[str, Any] = {}
    score_entries: List[Dict[str, Any]] = []
    errors: Dict[str, str] = {}
    total_score = 0.0
    total_possible = 0.0

    question_lookup = {str(q.id): q for q in survey.questions.order_by("order", "id")}

    for key, question in question_lookup.items():
        if question.qtype == "info":
            continue
        value = answers.get(key)
        if value in (None, "") and question.is_required:
            errors[key] = "This question is required."
            continue

        if question.qtype == "short-text":
            cleaned_answers[key] = str(value or "")
        elif question.qtype == "long-text":
            cleaned_answers[key] = str(value or "")
        elif question.qtype == "single-choice":
            if value is None:
                cleaned_answers[key] = None
            else:
                str_value = str(value)
                options = question.option_scores()
                if options and str_value not in options.keys() and str_value not in question.option_labels().keys():
                    errors[key] = "Select a valid option."
                    continue
                cleaned_answers[key] = str_value
        elif question.qtype == "multi-choice":
            items = value if isinstance(value, list) else []
            cleaned = []
            valid_options = set(question.option_scores().keys()) or set(question.option_labels().keys())
            for item in items:
                str_item = str(item)
                if valid_options and str_item not in valid_options:
                    continue
                cleaned.append(str_item)
            if question.is_required and not cleaned:
                errors[key] = "Select at least one option."
                continue
            cleaned_answers[key] = cleaned
        elif question.qtype in {"rating", "number", "scale"}:
            if value in ("", None):
                cleaned_answers[key] = None
            else:
                try:
                    cleaned_answers[key] = float(value)
                except (TypeError, ValueError):
                    errors[key] = "Enter a valid number."
                    continue
        else:
            cleaned_answers[key] = value

        if question.is_scored:
            score, max_possible = _evaluate_score(question, cleaned_answers.get(key))
            total_score += score
            total_possible += max_possible
            chart_payload = _individual_chart_payload(question, score, max_possible)
            score_entry: Dict[str, Any] = {
                "id": question.id,
                "score": round(score, 2),
                "maxScore": round(max_possible, 2),
            }
            if chart_payload:
                score_entry["chart"] = chart_payload
            score_entries.append(score_entry)

    if errors:
        return JsonResponse({"error": "Validation error", "details": errors}, status=400)

    summary = {
        "questions": score_entries,
        "totalScore": round(total_score, 2),
        "totalPossible": round(total_possible, 2),
        "percentage": round((total_score / total_possible) * 100, 2) if total_possible else None,
    }

    response, _created = CustomUserSurveyResponse.objects.update_or_create(
        participant=participant,
        defaults={
            "answers": cleaned_answers,
            "score_summary": summary,
        },
    )

    participant.status = "completed"
    if not participant.consented_at:
        participant.consented_at = timezone.now()
    participant.save(update_fields=["status", "consented_at", "updated_at"])

    return JsonResponse(
        {
            "participant": _participant_to_dict(participant),
            "survey": _survey_to_dict(survey, include_questions=False),
            "scoreSummary": response.score_summary or {},
        },
        status=200,
    )


@login_required
@require_http_methods(["GET"])
def api_survey_analytics(request, pk: int):
    if not _ensure_admin(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    survey = get_object_or_404(CustomUserSurvey, pk=pk)
    responses = CustomUserSurveyResponse.objects.filter(participant__survey=survey).select_related("participant")

    answers_by_question: Dict[int, List[Any]] = {q.id: [] for q in survey.questions.all()}
    score_entries_by_question: Dict[int, List[Dict[str, Any]]] = {q.id: [] for q in survey.questions.all()}

    for response in responses:
        answers = response.answers or {}
        summary = response.score_summary or {}
        summary_items = summary.get("questions", [])
        summary_lookup = {}
        for item in summary_items:
            if isinstance(item, dict) and "id" in item:
                summary_lookup[item["id"]] = item

        for question_id in answers_by_question.keys():
            key = str(question_id)
            if key in answers:
                answers_by_question[question_id].append(answers[key])

        for question_id, entry in summary_lookup.items():
            if question_id in score_entries_by_question:
                score_entries_by_question[question_id].append(entry)

    charts: List[Dict[str, Any]] = []
    for question in survey.questions.all():
        chart = _aggregate_question_chart(
            question,
            answers_by_question.get(question.id, []),
            score_entries_by_question.get(question.id, []),
        )
        if chart:
            charts.append(chart)

    return JsonResponse(
        {
            "survey": _survey_to_dict(survey, include_questions=False),
            "charts": charts,
            "responseCount": responses.count(),
        },
        status=200,
    )
