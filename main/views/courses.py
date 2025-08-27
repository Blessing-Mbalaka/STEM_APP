# main/views/courses.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

def courses(request):
    return render(request, "Courses.html")

@require_GET
def api_courses(request):
    """
    Minimal JSON for Courses page.
    Shape matches the frontend expectation:
    {
      "subjects": {
        "math": { "name": "...", "visual":[{title,duration}], "auditory":[...], "readwrite":[{title,author,pages}] },
        ...
      }
    }
    """
    from main.models.course import Course, CourseResource
    subjects = {}
    for course in Course.objects.filter(is_active=True):
        subj_key = course.subject.lower() if course.subject else course.title.lower()
        if subj_key not in subjects:
            subjects[subj_key] = {
                "name": course.title,
                "visual": [],
                "auditory": [],
                "readwrite": []
            }
        resources = CourseResource.objects.filter(course=course)
        for res in resources:
            entry = {
                "title": res.title,
                "description": res.description,
                "resource_type": res.resource_type,
                "url": res.url,
                "file": res.file.url if res.file else None
            }
            # Add extra fields for read/write
            if res.learning_style == "readwrite":
                entry["author"] = res.description or ""
                entry["pages"] = ""
            if res.learning_style == "visual":
                entry["duration"] = ""
            if res.learning_style == "auditory":
                entry["duration"] = ""
            subjects[subj_key][res.learning_style].append(entry)
    return JsonResponse({"subjects": subjects})
