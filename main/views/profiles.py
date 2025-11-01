from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json
from django.contrib.auth import get_user_model

User = get_user_model()

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

@login_required
@require_http_methods(["PATCH"])
def api_me(request):
    """PATCH /api/me — update current user and return canonical fields."""
    try:
        payload = json.loads(request.body.decode() or "{}")
    except Exception:
        payload = {}

    u = request.user
    # accept both camelCase and snake_case keys
    u.first_name = payload.get("firstName", payload.get("first_name", u.first_name))
    u.last_name  = payload.get("lastName",  payload.get("last_name",  u.last_name))
    u.email      = payload.get("email", u.email)
    # add other user fields as needed...
    u.save()

    # compute authoritative display_name (prefer submitted, then profile, then user names)
    display_name = payload.get("displayName") or payload.get("display_name")
    if not display_name and hasattr(u, "profile"):
        display_name = getattr(u.profile, "display_name", None)
    if not display_name:
        display_name = " ".join([n for n in (u.first_name, u.last_name) if n]).strip() or u.username

    # if profile model exists, persist display_name there too
    if hasattr(u, "profile"):
        try:
            u.profile.display_name = display_name
            u.profile.save()
        except Exception:
            pass

    # return both snake_case and camelCase so other pages keep working
    return JsonResponse({
        "id": u.id,
        "username": u.username,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "display_name": display_name,
        "firstName": u.first_name,
        "lastName": u.last_name,
        "displayName": display_name,
    })

def profiles(request):
    """Render Profiles page."""
    return render(request, "Profiles.html")