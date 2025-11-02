# main/views/forum.py
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods
import json
from django.shortcuts import get_object_or_404

from main.models.forum import ForumCategory, Post, PostLike, Thread
from main.utils.yaml_logger import (
    FORUM_QUESTIONS_FILE,
    append_yaml_record,
    log_student_search,
)


# ─── PAGE VIEW ────────────────────────────────────────────────
def forum(request):
    from main.models.chatbot_config import ChatbotConfig

    default_config = {
        "is_enabled": True,
        "mode": "gemini",
        "allow_internet_search": True,
        "maintenance_message": (
            "Our AI assistant is currently undergoing maintenance. "
            "Please add your question to the forum and a tutor will respond soon."
        ),
        "gemini_model": "",
        "external_api_base_url": "",
        "external_model": "",
        "ollama_api_base_url": "",
        "ollama_model": "",
    }

    try:
        config = ChatbotConfig.load()
        config_payload = config.as_dict(include_sensitive=False)
    except Exception:
        config_payload = default_config
    else:
        for key, value in default_config.items():
            config_payload.setdefault(key, value)

    return render(
        request,
        "Forum.html",
        {
            "chatbot_config_json": json.dumps(config_payload),
        },
    )


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
    GET  /api/forum/threads  -> return list of threads (include image_url from first post if present)
    POST /api/forum/threads  -> create a thread (accepts multipart/form-data with optional 'image')
    """
    if request.method == "GET":
        try:
            qs = Thread.objects.select_related("author", "category").annotate(posts_count=Count('posts')).order_by('-created_at')
            results = []
            for t in qs:
                # find first post with image (or None)
                first_post = Post.objects.filter(thread=t, image__isnull=False).order_by('created_at').first()
                image_url = None
                if first_post and getattr(first_post, 'image', None) and getattr(first_post.image, 'url', None):
                    image_url = request.build_absolute_uri(first_post.image.url)
                results.append({
                    "id": getattr(t, "id", None),
                    "slug": t.slug,
                    "title": t.title,
                    "body": t.body,
                    "author": t.author.username if t.author else None,
                    "created_at": t.created_at.isoformat() if getattr(t, 'created_at', None) else None,
                    "posts": getattr(t, 'posts_count', 0),
                    "image": image_url,           # short key used by client
                    "image_url": image_url,       # alternate key just in case
                    "category": t.category.slug if t.category else None,
                })
            # Return both keys so older/frontend code that expects either will work
            return JsonResponse({"results": results, "threads": results})
        except Exception as exc:
            # log minimal info to server console to help debugging
            import traceback, sys
            print("api_forum_threads error:", exc, file=sys.stderr)
            traceback.print_exc()
            # don't crash the frontend — return an empty list plus error hint
            return JsonResponse({"results": [], "threads": [], "error": "server_error"}, status=500)

    # POST -> create thread + initial post, save uploaded image to Post.image
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    # handle multipart/form-data or fallback to JSON
    if request.FILES or request.POST:
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        category_slug = request.POST.get('category')
        upload = request.FILES.get('image')
    else:
        try:
            payload = json.loads(request.body.decode() or "{}")
        except Exception:
            payload = {}
        title = (payload.get('title') or '').strip()
        body = (payload.get('body') or '').strip()
        category_slug = payload.get('category')
        upload = None

    if not title or not body:
        return JsonResponse({"error": "title & body required"}, status=400)

    category = None
    if category_slug:
        try:
            category = ForumCategory.objects.get(slug=category_slug)
        except ForumCategory.DoesNotExist:
            category = None

    thread = Thread.objects.create(title=title, body=body, author=request.user, category=category)

    # create initial post (so images attach to Post model which already has FileField)
    post = Post.objects.create(thread=thread, author=request.user, body=body)

    if upload:
        try:
            # remove any existing (unlikely) then save
            existing = getattr(post, 'image', None)
            if existing and getattr(existing, "name", None):
                try:
                    if existing.storage.exists(existing.name):
                        existing.storage.delete(existing.name)
                except Exception:
                    pass
            post.image.save(upload.name, upload, save=True)
        except Exception as e:
            return JsonResponse({"ok": True, "slug": thread.slug, "error": f"file save failed: {e}"}, status=500)

    image_url = None
    if getattr(post, 'image', None) and getattr(post.image, 'url', None):
        image_url = request.build_absolute_uri(post.image.url)

    return JsonResponse({"ok": True, "slug": thread.slug, "image_url": image_url})


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
                "image": request.build_absolute_uri(p.image.url) if p.image else None,
                "created_at": p.created_at.isoformat(),
                "likes": p.likes.count() if hasattr(p, 'likes') else 0,
            }
            for p in posts
        ]
        return JsonResponse({"results": data})

    # POST - Handle reply with potential image
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    # Accept FormData (files) or JSON
    if request.FILES or request.POST:
        body = request.POST.get("body", "").strip()
        upload = request.FILES.get("image")
    else:
        try:
            payload = json.loads(request.body.decode("utf-8"))
            body = (payload.get("body") or "").strip()
            upload = None
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not body:
        return JsonResponse({"error": "body required"}, status=400)

    # Create the post first
    post = Post.objects.create(thread=thread, author=request.user, body=body)

    # If an uploaded file exists, save it using the model field's storage.
    if upload:
        try:
            # If by any chance a file existed on this instance, remove it first
            existing = getattr(post, "image", None)
            if existing and getattr(existing, "name", None):
                try:
                    if existing.storage.exists(existing.name):
                        existing.storage.delete(existing.name)
                except Exception:
                    pass
            # Save new file via FileField API
            post.image.save(upload.name, upload, save=True)
        except Exception as e:
            # still return created post but indicate upload problem
            return JsonResponse({"ok": True, "id": post.id, "error": f"file save failed: {e}"}, status=500)

    image_url = request.build_absolute_uri(post.image.url) if getattr(post, "image", None) and getattr(post.image, "url", None) else None

    return JsonResponse({
        "ok": True,
        "id": post.id,
        "author": post.author.username,
        "body": post.body,
        "image": image_url,
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

