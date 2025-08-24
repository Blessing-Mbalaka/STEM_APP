# main/views/forum.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
import json

from main.models.forum import ForumCategory, Thread, Post, PostLike


# ─── PAGE VIEW ────────────────────────────────────────────────
def forum(request):
    return render(request, "Forum.html")


# ─── API ENDPOINTS ────────────────────────────────────────────

@require_GET
def api_forum_categories(request):
    """GET /api/forum/categories"""
    qs = ForumCategory.objects.annotate(num_threads=Count("threads"))
    data = [
        {
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "threads": c.num_threads,
        }
        for c in qs
    ]
    return JsonResponse({"results": data})


@require_http_methods(["GET", "POST"])
def api_forum_threads(request):
    """
    GET  /api/forum/threads?category=<slug>&q=<search>
    POST /api/forum/threads { "category": "<slug>", "title": "...", "body": "..." }
    """
    if request.method == "GET":
        qs = Thread.objects.select_related("category", "author").order_by("-created_at")

        cat = request.GET.get("category")
        if cat:
            qs = qs.filter(category__slug=cat)

        q = request.GET.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(body__icontains=q))

        data = [
            {
                "slug": t.slug,
                "title": t.title,
                "category": t.category.slug,
                "author": t.author.username,
                "created_at": t.created_at.isoformat(),
                "posts": t.posts.count(),
                "is_locked": t.is_locked,
            }
            for t in qs[:100]
        ]
        return JsonResponse({"results": data})

    # POST
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    cat_slug = payload.get("category")
    title = (payload.get("title") or "").strip()
    body = (payload.get("body") or "").strip()

    if not (cat_slug and title):
        return JsonResponse({"error": "category and title required"}, status=400)

    category = get_object_or_404(ForumCategory, slug=cat_slug)
    thread = Thread.objects.create(
        category=category, author=request.user, title=title, body=body
    )
    return JsonResponse({"ok": True, "slug": thread.slug})


@require_GET
def api_forum_thread_detail(request, slug: str):
    """GET /api/forum/threads/<slug>"""
    t = get_object_or_404(Thread.objects.select_related("category", "author"), slug=slug)
    payload = {
        "slug": t.slug,
        "title": t.title,
        "body": t.body,
        "category": t.category.slug,
        "author": t.author.username,
        "created_at": t.created_at.isoformat(),
        "is_locked": t.is_locked,
    }
    return JsonResponse(payload)


@require_http_methods(["GET", "POST"])
def api_forum_thread_posts(request, slug: str):
    """
    GET  /api/forum/threads/<slug>/posts
    POST /api/forum/threads/<slug>/posts { "body": "..." }
    """
    thread = get_object_or_404(Thread, slug=slug)

    if request.method == "GET":
        posts = Post.objects.select_related("author").filter(thread=thread)
        data = [
            {
                "id": p.id,
                "author": p.author.username,
                "body": p.body,
                "created_at": p.created_at.isoformat(),
                "likes": p.likes.count(),
            }
            for p in posts
        ]
        return JsonResponse({"results": data})

    # POST (reply)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    body = (payload.get("body") or "").strip()
    if not body:
        return JsonResponse({"error": "body required"}, status=400)

    post = Post.objects.create(thread=thread, author=request.user, body=body)
    return JsonResponse({"ok": True, "id": post.id})


@login_required
@require_http_methods(["POST"])
def api_forum_post_like(request, post_id: int):
    """
    POST /api/forum/posts/<id>/like (toggle like)
    """
    post = get_object_or_404(Post, id=post_id)

    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({"ok": True, "liked": liked, "likes": post.likes.count()})
