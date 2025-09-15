from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest


@login_required
def api_resources_library(request: HttpRequest):
    from main.models.resource import ResourceCategory, ResourceDocument

    terms = ResourceDocument.term_options()
    categories = []
    for category in ResourceCategory.objects.all().order_by("name"):
        documents_map = {term["value"]: [] for term in terms}
        for doc in category.documents.all().order_by("term", "-created_at", "title"):
            documents_map.setdefault(doc.term, []).append({
                "id": doc.id,
                "title": doc.title,
                "description": doc.description,
                "term": doc.term,
                "file": request.build_absolute_uri(doc.file.url) if doc.file else "",
                "uploaded_at": doc.created_at.isoformat(),
                "original_filename": doc.original_filename,
            })
        total = sum(len(items) for items in documents_map.values())
        categories.append({
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "total_documents": total,
            "documents": documents_map,
        })
    return JsonResponse({"categories": categories, "terms": terms})
