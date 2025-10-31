from django.http import FileResponse, Http404
from django.conf import settings
import os


def pdf_embed(request, path):
    """
    Serve PDF files for embedding with proper headers
    """
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        if os.path.exists(file_path) and file_path.endswith('.pdf'):
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = 'inline'
            return response
        else:
            raise Http404("PDF not found")
    except Exception:
        raise Http404("PDF not found")






