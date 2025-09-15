from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .chatbotmodel import ask_ollama

@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        prompt = (data.get("prompt") or "").strip()
        model = data.get("model")
        if not prompt:
            return JsonResponse({"error": "Prompt required"}, status=400)
        response = ask_ollama(prompt, model)
        if isinstance(response, str):
            if response.lower().startswith("sorry"):
                return JsonResponse({"error": response}, status=502)
            return JsonResponse({"response": response})
        return JsonResponse({"response": str(response)})
    return JsonResponse({"error": "Invalid request"}, status=400)
