import os, mimetypes
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils.encoding import smart_str
from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt            # ← removes X-Frame-Options header entirely
def pdf_embed(request, path):
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.isfile(full_path):
        raise Http404("PDF not found")

    content_type = mimetypes.guess_type(full_path)[0] or "application/pdf"
    f = open(full_path, "rb")
    resp = FileResponse(f, content_type=content_type)
    # Force inline display
    resp["Content-Disposition"] = f'inline; filename="{smart_str(os.path.basename(full_path))}"'
    return resp
