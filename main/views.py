# main/views.py
from django.shortcuts import render

def Tutors(request):
    return render(request, "Tutors.html")  # exact name, no "main/" prefix
