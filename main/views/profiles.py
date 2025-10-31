from django.shortcuts import render

def profiles(request):
    return render(request, "Profiles.html")



from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@csrf_exempt
@login_required
def upload_avatar(request):
    print("Upload avatar endpoint hit")  # Debugging: Check if the endpoint is called

    if request.method == 'POST' and request.FILES.get('avatar'):
        user = request.user
        avatar = request.FILES['avatar']
        print(f"Received file: {avatar.name}")  # Debugging: Log the received file name

        # Save the file to the user's profile
        if hasattr(user, 'profile'):
            try:
                user.profile.avatar = avatar
                user.profile.save()
                print(f"Avatar saved successfully: {user.profile.avatar.url}")  # Debugging: Log success
                return JsonResponse({'avatar_url': user.profile.avatar.url})
            except Exception as e:
                print(f"Error saving avatar: {e}")  # Debugging: Log any errors during save
                return JsonResponse({'error': 'Failed to save avatar'}, status=500)
        else:
            print("Profile not found for user")  # Debugging: Log if the profile is missing
            return JsonResponse({'error': 'Profile not found'}, status=404)
    
    print("No file uploaded or invalid request method")  # Debugging: Log if no file is uploaded
    return JsonResponse({'error': 'No file uploaded'}, status=400)