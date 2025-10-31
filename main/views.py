from django.shortcuts import render

def Tutors(request):
    """
    Simple view that returns the tutors page (literal copy of classes).
    """
    return render(request, 'main/tutors.html')