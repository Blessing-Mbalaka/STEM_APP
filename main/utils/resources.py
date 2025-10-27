from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from django.conf import settings

from main.models.course import CourseResource
from main.models.resource import ResourceDocument

from .yaml_logger import RESOURCE_LINKS_FILE, write_yaml_records


def _build_media_url(path: str | None) -> str:
    if not path:
        return ""
    media_url = getattr(settings, "MEDIA_URL", "") or "/media/"
    return f"{media_url.rstrip('/')}/{path.lstrip('/')}"


def snapshot_resource_links() -> List[Dict[str, str]]:
    """
    Build a snapshot of all course and shared resource links and persist them
    to the resource_links YAML file. Returns the list of records.
    """
    records: List[Dict[str, str]] = []
    seen = set()

    # Course resources (videos, documents, quizzes, etc.)
    for resource in CourseResource.objects.select_related("course").all():
        url = resource.url or _build_media_url(resource.file.name if resource.file else "")
        if not url:
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
            "url": url,
        })

    # Administrator uploaded resource documents
    for document in ResourceDocument.objects.select_related("category").all():
        url = _build_media_url(document.file.name if document.file else "")
        if not url:
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
            "url": url,
        })

    write_yaml_records(RESOURCE_LINKS_FILE, records)
    return records
