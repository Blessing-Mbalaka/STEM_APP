from main.utils.mail import send_email
from django.http import JsonResponse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from main.models import CustomUser

token_generator = PasswordResetTokenGenerator()

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        users = CustomUser.objects.filter(email=email)
        if not users.exists():
            return JsonResponse({"error": "User not found"}, status=404)
        elif users.count() > 1:
            return JsonResponse({"error": "Multiple users found"}, status=400)
        user = users.first()

        # Generate token and UID
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_url = request.build_absolute_uri(reverse('reset_password', kwargs={'uidb64': uid, 'token': token}))

        # Send email with reset link
        send_email(
            subject='Password Reset Request',
            message=f'Click the link below to reset your password: {reset_url}',
            recipient_list=[email],
        )
        return JsonResponse({'message': 'Password reset email sent successfully.'})
    return JsonResponse({'error': 'Invalid request.'}, status=400)

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        return JsonResponse({'error': 'Invalid link.'}, status=400)

    if not token_generator.check_token(user, token):
        return JsonResponse({'error': 'Invalid or expired token.'}, status=400)

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if not new_password:
            return JsonResponse({'error': 'New password required.'}, status=400)

        user.set_password(new_password)
        user.save()

        # Send confirmation email
        send_email(
            subject='Password Reset Successful',
            message='Your password has been successfully reset.',
            recipient_list=[user.email],
        )
        return JsonResponse({'message': 'Password reset successful.'})
    return JsonResponse({'error': 'Invalid request.'}, status=400)