from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urlparse

from django.conf import settings

from main.models.course import CourseResource
from main.models.resource import ResourceDocument

from .yaml_logger import RESOURCE_LINKS_FILE, write_yaml_records


def _build_media_url(path: str | None) -> str:
    if not path:
        return ""
    media_url = getattr(settings, "MEDIA_URL", "") or "/media/"
    return f"{media_url.rstrip('/')}/{path.lstrip('/')}"


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a", "about", "an", "and", "are", "can", "do", "does", "explain",
    "for", "from", "how", "i", "in", "is", "it", "me", "of", "on",
    "please", "the", "to", "what", "when", "where", "which", "why", "with",
}
_QUERY_EXPANSIONS = {
    "algebra": {"equation", "solve", "function"},
    "cell": {"dna", "nucleus", "mitosis", "meiosis"},
    "derivative": {"calculus", "function"},
    "differentiation": {"calculus", "derivative"},
    "dna": {"genetics", "nucleus", "protein", "synthesis"},
    "electricity": {"circuit", "current", "electronics", "voltage"},
    "equation": {"algebra", "solve", "function"},
    "force": {"energy", "motion", "momentum", "work"},
    "genetics": {"dna", "nucleus", "protein", "synthesis"},
    "integration": {"calculus", "function"},
    "newton": {"force", "motion", "momentum"},
    "photosynthesis": {"biology", "cell", "life", "plant"},
    "reproduction": {"gametogenesis", "hormone", "menopause"},
}
_SUBJECT_KEYWORDS = {
    "accounting": {"accounting", "balance", "ledger"},
    "business": {"business", "management"},
    "economics": {"economics", "macro", "micro"},
    "english": {"english", "essay", "literature", "poetry", "writing"},
    "geography": {"climate", "geography", "geomorphology"},
    "history": {"history", "nazi"},
    "life science": {
        "biology", "cell", "dna", "genetics", "life", "meiosis", "mitosis",
        "nucleus", "photosynthesis", "protein", "reproduction",
    },
    "math": {
        "algebra", "calculus", "derivative", "equation", "finance", "function",
        "integration", "math", "mathematics", "probability", "sequence", "solve",
    },
    "physics": {
        "acceleration", "circuit", "electricity", "energy", "force", "impulse",
        "momentum", "motion", "newton", "physics", "projectile", "velocity", "work",
    },
}


def _normalise_tokens(text: str) -> set[str]:
    tokens = set(_TOKEN_RE.findall((text or "").casefold())) - _STOP_WORDS
    aliases = set()
    for token in tokens:
        if token in {"maths", "mathematics"}:
            aliases.add("math")
        if token.endswith("s") and len(token) > 4:
            aliases.add(token[:-1])
    return tokens | aliases


def _is_usable_url(url: str) -> bool:
    if not url or "\ufffd" in url:
        return False
    if url.startswith("/"):
        return True
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_resource_links() -> List[Dict[str, str]]:
    """Build structured links from active courses and the resource library."""
    records: List[Dict[str, str]] = []
    seen = set()

    # Course resources (videos, documents, quizzes, etc.)
    for resource in CourseResource.objects.select_related("course").filter(course__is_active=True):
        url = resource.url or _build_media_url(resource.file.name if resource.file else "")
        if not _is_usable_url(url):
            continue
        key = (url, resource.title, resource.course_id)
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "title": resource.title,
            "description": resource.description or "",
            "resource_type": resource.resource_type or "",
            "course": resource.course.title if resource.course_id else "",
            "learning_style": resource.learning_style or "",
            "resource_id": str(resource.id),
            "url": url,
        })

    # Administrator uploaded resource documents
    for document in ResourceDocument.objects.select_related("category").all():
        url = _build_media_url(document.file.name if document.file else "")
        if not _is_usable_url(url):
            continue
        key = (url, document.title, getattr(document.category, "id", None))
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "title": document.title,
            "description": document.description or "",
            "category": document.category.name if document.category_id else "",
            "term": document.term or "",
            "resource_type": "document",
            "resource_id": str(document.id),
            "url": url,
        })

    return records


def snapshot_resource_links() -> List[Dict[str, str]]:
    """Persist and return a snapshot of all usable learning-resource links."""
    records = build_resource_links()

    write_yaml_records(RESOURCE_LINKS_FILE, records)
    return records


def suggest_resource_links(query: str, *, limit: int = 3) -> List[Dict[str, str]]:
    """Return a few learning resources ranked against the student's question."""
    query_tokens = _normalise_tokens(query)
    if len(query_tokens) > 1:
        # In natural questions "how does X work?" is conversational rather than
        # a request for the physics topic named Work.
        query_tokens.discard("work")
    if not query_tokens or limit <= 0:
        return []

    expanded_tokens = set(query_tokens)
    for token in query_tokens:
        expanded_tokens.update(_QUERY_EXPANSIONS.get(token, set()))

    detected_subjects = {
        subject
        for subject, keywords in _SUBJECT_KEYWORDS.items()
        if expanded_tokens & keywords
    }
    ranked = []
    for position, record in enumerate(build_resource_links()):
        title_tokens = _normalise_tokens(record.get("title", ""))
        description_tokens = _normalise_tokens(record.get("description", ""))
        grouping_tokens = _normalise_tokens(
            " ".join((record.get("course", ""), record.get("category", "")))
        )
        score = (
            10 * len(expanded_tokens & title_tokens)
            + 3 * len(expanded_tokens & description_tokens)
            + 5 * len(expanded_tokens & grouping_tokens)
        )
        grouping_text = " ".join((record.get("course", ""), record.get("category", ""))).casefold()
        if any(subject in grouping_text for subject in detected_subjects):
            score += 6
        if record.get("resource_type") in {"video", "youtube"}:
            score += 1
        if score <= 0:
            continue
        ranked.append((score, -position, record))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [record for _, _, record in ranked[:limit]]
