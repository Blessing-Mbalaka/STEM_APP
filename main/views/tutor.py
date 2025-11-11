from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta, datetime
from django.contrib.auth import get_user_model
from django.db.models import Q

from main.utils.roles import user_has_role, ROLE_ADMIN, ROLE_TUTOR

# Import models (with fallback if they don't exist yet)
try:
    from main.models import TutorSession, TutorMessage
except ImportError:
    TutorSession = None
    TutorMessage = None

# Import forms (create simple fallback if forms don't exist)
try:
    from main.forms import SessionBookingForm, MessageForm
except ImportError:
    from django import forms
    
    class SessionBookingForm(forms.Form):
        title = forms.CharField(max_length=200)
        description = forms.CharField(widget=forms.Textarea)
        subject = forms.CharField(max_length=100)
        scheduled_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
        duration_minutes = forms.IntegerField(initial=60)
    
    class MessageForm(forms.Form):
        subject = forms.CharField(max_length=200)
        content = forms.CharField(widget=forms.Textarea)

User = get_user_model()

def generate_meeting_link(session):
    """Generate a meeting link for the session"""
    # Using Jitsi Meet (free, no API key required)
    return f"https://meet.jit.si/stem-session-{session.id}-{session.tutor.id}"

def send_session_confirmation_email(session):
    """Send confirmation email with meeting link"""
    subject = f"Tutoring Session Confirmed: {session.title}"
    
    # Format the scheduled time
    session_time = session.scheduled_time.strftime('%B %d, %Y at %I:%M %p')
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #24adb7;">Your Tutoring Session is Confirmed! 🎓</h2>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Session Details:</h3>
            <p><strong>Subject:</strong> {session.subject}</p>
            <p><strong>Title:</strong> {session.title}</p>
            <p><strong>Date & Time:</strong> {session_time}</p>
            <p><strong>Duration:</strong> {session.duration_minutes} minutes</p>
            <p><strong>Tutor:</strong> {session.tutor.get_full_name() or session.tutor.email}</p>
        </div>
        
        <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <h3 style="margin-top: 0; color: #155724;">Ready to Join Your Session?</h3>
            <p style="margin-bottom: 20px;">Click the button below to join your video session:</p>
            <a href="{session.meeting_link}" 
               style="background: #28a745; color: white; padding: 15px 30px; 
                      text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                🎥 Join Video Session
            </a>
            <p style="margin-top: 15px; font-size: 14px; color: #666;">
                Please join 5 minutes before the scheduled time
            </p>
        </div>
        
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h4 style="margin-top: 0;">Important Notes:</h4>
            <ul style="margin-bottom: 0;">
                <li>Make sure you have a stable internet connection</li>
                <li>Test your camera and microphone beforehand</li>
                <li>Have your materials ready (notebook, textbook, etc.)</li>
                <li>Join from a quiet environment</li>
            </ul>
        </div>
        
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            If you have any issues joining the session, please contact support or message your tutor directly.
        </p>
    </div>
    """
    
    plain_content = f"""
    Your Tutoring Session is Confirmed!
    
    Session Details:
    - Subject: {session.subject}
    - Title: {session.title}
    - Date & Time: {session_time}
    - Duration: {session.duration_minutes} minutes
    - Tutor: {session.tutor.get_full_name() or session.tutor.email}
    
    Meeting Link: {session.meeting_link}
    
    Please join 5 minutes before the scheduled time.
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_content,
            html_message=html_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@stemlms.com'),
            recipient_list=[session.student.email, session.tutor.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

@login_required
def confirm_session(request, session_id):
    """Confirm a tutoring session and generate meeting link"""
    session = get_object_or_404(TutorSession, id=session_id)
    
    # Only tutor or admin can confirm
    if request.user != session.tutor and not user_has_role(request.user, ROLE_ADMIN):
        return HttpResponseForbidden()
    
    if request.method == 'POST' and session.status == 'pending':
        # Generate meeting link
        session.meeting_link = generate_meeting_link(session)
        session.status = 'confirmed'
        session.save()
        
        # Send confirmation email
        email_sent = send_session_confirmation_email(session)
        
        if email_sent:
            messages.success(request, f'Session confirmed! Meeting link sent to {session.student.email}')
        else:
            messages.warning(request, 'Session confirmed, but email notification failed.')
        
        return redirect('tutor_dashboard')
    
    return render(request, 'main/confirm_session.html', {'session': session})

@login_required
def video_session(request, session_id):
    """Video session page where students and tutors meet"""
    session = get_object_or_404(TutorSession, id=session_id)
    
    # Verify user is part of this session
    if request.user not in [session.student, session.tutor]:
        messages.error(request, 'You are not authorized to join this session.')
        return redirect('dashboard')
    
    # Check session status and timing
    now = timezone.now()
    session_start = session.scheduled_time
    session_end = session_start + timedelta(minutes=session.duration_minutes)
    
    if session.status != 'confirmed':
        messages.error(request, 'This session has not been confirmed yet.')
        return redirect('dashboard')
    
    # Allow joining 10 minutes early
    if now < session_start - timedelta(minutes=10):
        messages.info(request, f'Session starts at {session_start.strftime("%I:%M %p")}. Please return closer to the scheduled time.')
        return redirect('dashboard')
    
    # Session expires 30 minutes after end time
    if now > session_end + timedelta(minutes=30):
        messages.info(request, 'This session has ended.')
        return redirect('dashboard')
    
    context = {
        'session': session,
        'is_tutor': request.user == session.tutor,
        'is_student': request.user == session.student,
        'session_start': session_start,
        'session_end': session_end,
        'can_start': now >= session_start - timedelta(minutes=5),
    }
    
    return render(request, 'main/video_session.html', context)

@login_required
def complete_session(request, session_id):
    """Mark session as completed (tutor only)"""
    session = get_object_or_404(TutorSession, id=session_id)
    
    if request.method == 'POST' and request.user == session.tutor:
        session.status = 'completed'
        session.save()
        
        messages.success(request, 'Session marked as completed!')
        return JsonResponse({'success': True, 'redirect': reverse('tutor_dashboard')})
    
    return JsonResponse({'success': False, 'error': 'Unauthorized'})

@login_required
def cancel_session(request, session_id):
    """Cancel a session"""
    session = get_object_or_404(TutorSession, id=session_id)
    
    # Student or tutor can cancel
    if request.user not in [session.student, session.tutor]:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        session.status = 'cancelled'
        session.save()
        
        # Send cancellation email
        subject = f"Session Cancelled: {session.title}"
        message = f"The tutoring session scheduled for {session.scheduled_time.strftime('%B %d, %Y at %I:%M %p')} has been cancelled."
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@stemlms.com'),
                recipient_list=[session.student.email, session.tutor.email],
                fail_silently=True,
            )
        except:
            pass
        
        messages.success(request, 'Session cancelled successfully.')
        return redirect('dashboard')
    
    return render(request, 'main/cancel_session.html', {'session': session})

@login_required
def tutor_dashboard(request):
    """Tutor dashboard showing all sessions"""
    if not TutorSession:
        # Fallback if model doesn't exist
        return render(request, 'main/tutor_dashboard.html', {
            'sessions': [],
            'is_tutor': user_has_role(request.user, ROLE_TUTOR, ROLE_ADMIN),
            'error': 'Tutor session model not available. Please run migrations.'
        })
    
    # Check if user is tutor (staff) or student
    if user_has_role(request.user, ROLE_TUTOR, ROLE_ADMIN):
        # Tutor view - show sessions they're tutoring
        sessions = TutorSession.objects.filter(tutor=request.user).order_by('-scheduled_time')
        is_tutor = True
    else:
        # Student view - show sessions they've booked
        sessions = TutorSession.objects.filter(student=request.user).order_by('-scheduled_time')
        is_tutor = False
    
    context = {
        'sessions': sessions,
        'is_tutor': is_tutor,
        'pending_sessions': sessions.filter(status='pending'),
        'confirmed_sessions': sessions.filter(status='confirmed'),
        'completed_sessions': sessions.filter(status='completed'),
    }
    
    return render(request, 'main/tutor_dashboard.html', context)

@login_required
def book_session(request):
    """Book a new tutoring session"""
    if not TutorSession:
        messages.error(request, 'Tutoring system not available. Please contact administrator.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SessionBookingForm(request.POST)
        if form.is_valid():
            # Get available tutors (staff users)
            tutors = User.objects.filter(Q(is_staff=True) | Q(is_tutor=True) | Q(is_superuser=True))
            if not tutors.exists():
                messages.error(request, 'No tutors available at the moment.')
                return redirect('book_session')
            
            # For now, assign to first available tutor
            # In production, you might want to implement tutor selection logic
            tutor = tutors.first()
            
            session = TutorSession.objects.create(
                tutor=tutor,
                student=request.user,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                subject=form.cleaned_data['subject'],
                scheduled_time=form.cleaned_data['scheduled_time'],
                duration_minutes=form.cleaned_data['duration_minutes']
            )
            
            messages.success(request, f'Session booked successfully! Your tutor ({tutor.get_full_name() or tutor.email}) will confirm soon.')
            return redirect('tutor_dashboard')
    else:
        form = SessionBookingForm()
    
    # Get available tutors for display
    tutors = User.objects.filter(Q(is_staff=True) | Q(is_tutor=True) | Q(is_superuser=True))
    subjects = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science', 'Engineering', 'Other']
    
    context = {
        'form': form,
        'tutors': tutors,
        'subjects': subjects,
    }
    
    return render(request, 'main/book_session.html', context)

@login_required
def send_message(request):
    """Send a message to tutor or student"""
    if not TutorMessage:
        messages.error(request, 'Messaging system not available.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            # You'll need to implement recipient selection logic
            # For now, this is a placeholder
            messages.success(request, 'Message sent successfully!')
            return redirect('tutor_dashboard')
    else:
        form = MessageForm()
    
    return render(request, 'main/send_message.html', {'form': form})

@login_required
def tutor_admin(request):
    """Tutor admin panel for managing courses and materials"""
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_TUTOR):
        return HttpResponseForbidden("Forbidden")

    # Get courses managed by this tutor
    try:
        from main.models import Course
        courses = Course.objects.filter(instructor=request.user)
    except Exception:
        courses = []

    context = {
        'courses': courses,
        'tutor': request.user,
    }
    return render(request, 'TutorAdmin.html', context)

@login_required
def api_tutor_courses(request):
    """API endpoint for tutor's courses"""
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_TUTOR):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        from main.models import Course
        courses = Course.objects.filter(instructor=request.user)
        courses_data = []
        for course in courses:
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'subject': course.subject,
                'description': course.description,
                'is_active': course.is_active,
                'created_at': course.created_at.isoformat() if hasattr(course, 'created_at') else None,
            })
        return JsonResponse({'courses': courses_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_tutor_course_detail(request, course_id):
    """API endpoint for specific course details"""
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_TUTOR):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        from main.models import Course, CourseResource
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        resources = CourseResource.objects.filter(course=course)
        
        course_data = {
            'id': course.id,
            'title': course.title,
            'subject': course.subject,
            'description': course.description,
            'is_active': course.is_active,
            'resources': [{
                'id': res.id,
                'title': res.title,
                'description': res.description,
                'resource_type': res.resource_type,
                'file_url': res.file.url if res.file else None,
            } for res in resources]
        }
        return JsonResponse({'course': course_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_tutor_course_add_resource(request, course_id):
    """API endpoint to add resources to a course"""
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_TUTOR):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        from main.models import Course, CourseResource
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        resource_type = request.POST.get('resource_type', 'document')
        file = request.FILES.get('file')
        
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        resource = CourseResource.objects.create(
            course=course,
            title=title,
            description=description,
            resource_type=resource_type,
            file=file,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'resource': {
                'id': resource.id,
                'title': resource.title,
                'description': resource.description,
                'resource_type': resource.resource_type,
                'file_url': resource.file.url if resource.file else None,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_tutor_resource_detail(request, resource_id):
    """API endpoint for specific resource details"""
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_TUTOR):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        from main.models import CourseResource
        resource = get_object_or_404(CourseResource, id=resource_id, course__instructor=request.user)
        
        resource_data = {
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'resource_type': resource.resource_type,
            'file_url': resource.file.url if resource.file else None,
            'course_id': resource.course.id,
            'course_title': resource.course.title,
        }
        return JsonResponse({'resource': resource_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_tutor_course_thumbnail(request, course_id):
    """API endpoint to update course thumbnail"""
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_TUTOR):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        from main.models import Course
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        
        thumbnail = request.FILES.get('thumbnail')
        if not thumbnail:
            return JsonResponse({'error': 'Thumbnail file is required'}, status=400)
        
        course.thumbnail = thumbnail
        course.save()
        
        return JsonResponse({
            'success': True,
            'thumbnail_url': course.thumbnail.url if course.thumbnail else None
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_tutor_course_reorder(request, course_id):
    """API endpoint to reorder course resources"""
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_TUTOR):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        from main.models import Course, CourseResource
        import json
        
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        
        # Expecting JSON data with resource order
        data = json.loads(request.body)
        resource_order = data.get('resource_order', [])
        
        for index, resource_id in enumerate(resource_order):
            CourseResource.objects.filter(
                id=resource_id, 
                course=course
            ).update(order=index)
        
        return JsonResponse({'success': True, 'message': 'Resources reordered successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_course_sequence(request, course_id):
    """API endpoint for course learning sequence"""
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_TUTOR):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        from main.models import Course, CourseResource
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        resources = CourseResource.objects.filter(course=course).order_by('order', 'created_at')
        
        sequence = []
        for resource in resources:
            sequence.append({
                'id': resource.id,
                'title': resource.title,
                'type': resource.resource_type,
                'order': getattr(resource, 'order', 0),
                'completed': False,  # You can implement completion tracking
            })
        
        return JsonResponse({'sequence': sequence})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_course_poll_vote(request, course_id, poll_id):
    """API endpoint for course polls/voting"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # Placeholder for poll functionality
        vote_option = request.POST.get('option')
        
        # You can implement actual poll logic here
        return JsonResponse({
            'success': True,
            'message': f'Vote recorded for option: {vote_option}',
            'poll_id': poll_id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
