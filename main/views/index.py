from django.shortcuts import render

def index(request):
    return render(request, "Index.html")


def resources(request):
    return render(request, "Resources.html")
