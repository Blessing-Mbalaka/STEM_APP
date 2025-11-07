from main.utils.mail import send_email
from django.http import JsonResponse

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Example usage of the send_email function
        send_email(
            subject='Password Reset Request',
            message='Click the link below to reset your password.',
            recipient_list=[email],
        )
        return JsonResponse({'message': 'Password reset email sent successfully.'})
    return JsonResponse({'error': 'Invalid request.'}, status=400)

def reset_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')

        # Logic to reset the password (e.g., update the database)
        # Assume the password reset logic is successful

        # Send confirmation email
        send_email(
            subject='Password Reset Successful',
            message='Your password has been successfully reset.',
            recipient_list=[email],
        )
        return JsonResponse({'message': 'Password reset successful.'})
    return JsonResponse({'error': 'Invalid request.'}, status=400)