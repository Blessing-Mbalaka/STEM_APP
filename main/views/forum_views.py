from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os

from main.models import Thread, Post

@login_required
@require_http_methods(["POST"])
def create_post(request, slug):
    """POST /api/forum/threads/<slug>/posts  - accepts multipart/form-data with 'body' and optional 'image'"""
    thread = get_object_or_404(Thread, slug=slug)
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error': 'No body provided'}, status=400)

    # create Post first (so we have an instance to attach file to)
    p = Post.objects.create(thread=thread, author=request.user, body=body)

    img = request.FILES.get('image')
    if img:
        # if there is an existing file on the instance, remove it first so the new file "overwrites"
        try:
            existing = getattr(p, 'image', None)
            if existing and existing.name:
                # delete file from storage if it exists
                if existing.storage.exists(existing.name):
                    existing.storage.delete(existing.name)
        except Exception:
            pass

        # save the new file
        p.image.save(img.name, img, save=True)

    # return helpful payload including the absolute image URL (if present)
    image_url = None
    if getattr(p, 'image', None) and getattr(p.image, 'url', None):
        image_url = request.build_absolute_uri(p.image.url)

    return JsonResponse({
        'ok': True,
        'id': p.id,
        'created_at': p.created_at.isoformat(),
        'image_url': image_url,
    })