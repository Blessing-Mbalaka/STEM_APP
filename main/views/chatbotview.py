from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .chatbot import ask_ollama

@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        prompt = data.get("prompt", "")
        model = data.get("model", "gemma3")
        response = ask_ollama(prompt, model)
        return JsonResponse({"response": response})
    return JsonResponse({"error": "Invalid request"}, status=400)