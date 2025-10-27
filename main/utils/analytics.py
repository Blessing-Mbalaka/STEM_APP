from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from django.apps import apps
from django.db.models import Count
from django.utils import timezone

from main.models.classes import ClassSession, Reservation
from main.models.course import Course, Enrollment
from main.models.user import CustomUser, Profile

from .yaml_logger import (
    CHATBOT_HISTORY_FILE,
    FORUM_QUESTIONS_FILE,
    STUDENT_SEARCHES_FILE,
    load_yaml_records,
)
from .resources import snapshot_resource_links


def _normalize_timestamp(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def collect_dashboard_metrics() -> Dict[str, Any]:
    now = timezone.now()

    total_users = CustomUser.objects.count()
    total_tutors = CustomUser.objects.filter(is_tutor=True).count()
    total_students = CustomUser.objects.filter(is_tutor=False).count()

    try:
        TutorSession = apps.get_model("main", "TutorSession")
    except LookupError:
        TutorSession = None

    if TutorSession:
        sessions_qs = TutorSession.objects.all()
        sessions_total = sessions_qs.count()
        sessions_by_status = list(
            sessions_qs.values("status").annotate(total=Count("id")).order_by("-total")
        )
        upcoming_sessions = sessions_qs.filter(scheduled_time__gte=now).count()
        completed_sessions = sessions_qs.filter(status="completed").count()
    else:
        sessions_total = 0
        sessions_by_status = []
        upcoming_sessions = 0
        completed_sessions = 0

    classes_upcoming = ClassSession.objects.filter(starts_at__gte=now).count()
    reservations_by_status = list(
        Reservation.objects.values("status").annotate(total=Count("id")).order_by("-total")
    )

    enrollment_stats = list(
        Enrollment.objects.values("status").annotate(total=Count("id")).order_by("-total")
    )

    courses_by_level = list(
        Course.objects.values("level").annotate(total=Count("id")).order_by("-total")
    )

    profiles = Profile.objects.select_related("user")

    grade_distribution = list(
        profiles.exclude(grade="")
        .values("grade")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    streams = list(
        profiles.exclude(stream="")
        .values("stream")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    schools = [p["school"] for p in profiles.exclude(school="").values("school")]
    top_schools = Counter(schools).most_common(5)

    recent_questions = load_yaml_records(FORUM_QUESTIONS_FILE)[-5:]
    recent_questions = [
        {
            **item,
            "created_at": _normalize_timestamp(item.get("created_at")),
        }
        for item in recent_questions
    ][::-1]

    chatbot_history = load_yaml_records(CHATBOT_HISTORY_FILE)[-5:]

    resource_links = snapshot_resource_links()
    chatbot_history = [
        {
            **item,
            "timestamp": _normalize_timestamp(item.get("timestamp")),
        }
        for item in chatbot_history
    ][::-1]

    search_records_all = load_yaml_records(STUDENT_SEARCHES_FILE)
    term_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    valid_records = []
    for record in search_records_all:
        query = (record.get("query") or "").strip()
        if query:
            term_counts[query.lower()] += 1
        source = (record.get("source") or "unspecified").strip() or "unspecified"
        source_counts[source] += 1
        valid_records.append(record)

    recent_searches = [
        {
            "query": rec.get("query", ""),
            "timestamp": _normalize_timestamp(rec.get("timestamp")),
            "source": rec.get("source", "unspecified"),
            "actor": rec.get("actor", {}),
            "metadata": rec.get("metadata", {}),
        }
        for rec in valid_records[-10:]
    ][::-1]

    return {
        "counts": {
            "users": total_users,
            "students": total_students,
            "tutors": total_tutors,
            "sessions_total": sessions_total,
            "sessions_upcoming": upcoming_sessions,
            "sessions_completed": completed_sessions,
            "classes_upcoming": classes_upcoming,
        },
        "sessions_by_status": sessions_by_status,
        "reservations_by_status": reservations_by_status,
        "enrollments": enrollment_stats,
        "courses_by_level": courses_by_level,
        "grade_distribution": grade_distribution,
        "streams": streams,
        "top_schools": [
            {"school": name, "total": total} for name, total in top_schools
        ],
        "recent_forum_questions": recent_questions,
        "recent_chatbot_interactions": chatbot_history,
        "resource_links": resource_links,
        "student_searches": recent_searches,
        "search_summary": {
            "total_queries": len(valid_records),
            "top_terms": [
                {"term": term, "total": total}
                for term, total in term_counts.most_common(5)
            ],
            "by_source": [
                {"source": source, "total": total}
                for source, total in source_counts.most_common()
            ],
        },
    }
