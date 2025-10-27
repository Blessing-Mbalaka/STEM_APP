# main/views/forum.py
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

import json
from main.models.forum import ForumCategory, Post, PostLike, Thread
from main.utils.yaml_logger import (
    FORUM_QUESTIONS_FILE,
    append_yaml_record,
    log_student_search,
)


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
    POST /api/forum/threads (with FormData for images)
    """
    if request.method == "GET":
        qs = Thread.objects.select_related("category", "author").order_by("-created_at")

        cat = request.GET.get("category")
        if cat:
            qs = qs.filter(category__slug=cat)

        q = (request.GET.get("q") or "").strip()
        if q:
            log_student_search(
                q,
                user=request.user if request.user.is_authenticated else None,
                source="forum_threads",
                metadata={
                    "category": cat or "",
                    "path": "api/forum/threads",
                },
            )
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

    # POST - Handle thread creation
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    # Check if request contains files (FormData) or JSON
    if request.FILES or request.POST:
        # FormData request
        cat_slug = request.POST.get("category")
        title = (request.POST.get("title") or "").strip()
        body = (request.POST.get("body") or "").strip()
        image = request.FILES.get("image")  # For future thread images
    else:
        # JSON request (fallback)
        try:
            payload = json.loads(request.body.decode("utf-8"))
            cat_slug = payload.get("category")
            title = (payload.get("title") or "").strip()
            body = (payload.get("body") or "").strip()
            image = None
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not (cat_slug and title):
        return JsonResponse({"error": "category and title required"}, status=400)

    category = get_object_or_404(ForumCategory, slug=cat_slug)
    
    thread = Thread.objects.create(
        category=category, 
        author=request.user, 
        title=title, 
        body=body, 
        is_locked=False
    )
    append_yaml_record(
        FORUM_QUESTIONS_FILE,
        {
            "id": thread.id,
            "slug": thread.slug,
            "title": thread.title,
            "body": thread.body,
            "category": {
                "id": category.id,
                "slug": category.slug,
                "name": category.name,
            },
            "author": {
                "id": request.user.id,
                "username": request.user.username,
                "display_name": getattr(request.user, "display_name", ""),
            },
            "created_at": (thread.created_at or timezone.now()).isoformat(),
        },
        max_entries=1000,
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
    POST /api/forum/threads/<slug>/posts (with FormData for images)
    """
    thread = get_object_or_404(Thread, slug=slug)

    if request.method == "GET":
        posts = Post.objects.select_related("author").filter(thread=thread)
        data = [
            {
                "id": p.id,
                "author": p.author.username,
                "body": p.body,
                "image": request.build_absolute_uri(p.image.url) if p.image else None,  # Full URL for images
                "created_at": p.created_at.isoformat(),
                "likes": p.likes.count() if hasattr(p, 'likes') else 0,
            }
            for p in posts
        ]
        return JsonResponse({"results": data})

    # POST - Handle reply with potential image
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    # Check if request contains files (FormData) or JSON
    if request.FILES or request.POST:
        # FormData request (with potential image)
        body = request.POST.get("body", "").strip()
        image = request.FILES.get("image")
    else:
        # JSON request (fallback for backward compatibility)
        try:
            payload = json.loads(request.body.decode("utf-8"))
            body = (payload.get("body") or "").strip()
            image = None
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not body:
        return JsonResponse({"error": "body required"}, status=400)

    # Create the post with image
    post = Post.objects.create(
        thread=thread, 
        author=request.user, 
        body=body,
        image=image  # This will be None if no image uploaded
    )
    
    return JsonResponse({
        "ok": True, 
        "id": post.id,
        "author": post.author.username,
        "body": post.body,
        "image": request.build_absolute_uri(post.image.url) if post.image else None,
        "created_at": post.created_at.isoformat()
    })

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


# Should handle file uploads in the POST method:
def create_post(request):
    if request.method == 'POST':
        # Handle image upload
        image = request.FILES.get('image')  # or 'attachment'
        post = Post.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            image=image,  # Save the uploaded image
            author=request.user
        )

