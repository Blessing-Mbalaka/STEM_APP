from django.shortcuts import render, get_object_or_404
from main.models import Session

def video_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    is_tutor = request.user == session.tutor  # Check if the logged-in user is the tutor for the session
    can_start = session.can_start()  # Assuming `can_start` is a method or property of the `Session` model

    context = {
        'session': session,
        'is_tutor': is_tutor,
        'can_start': can_start,
    }
    return render(request, 'main/video_session.html', context)