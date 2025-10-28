from django.shortcuts import render, redirect

from main.utils.roles import get_primary_role, ROLE_ADMIN, ROLE_TUTOR

def index(request):
    if request.user.is_authenticated:
        role = get_primary_role(request.user)
        if role == ROLE_ADMIN:
            return redirect("/administrator/")
        if role == ROLE_TUTOR:
            return redirect("/tutor/admin/")
    return render(request, "Index.html")


def resources(request):
    return render(request, "Resources.html")
