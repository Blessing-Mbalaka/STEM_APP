import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Update if your Ollama server runs elsewhere

def ask_ollama(prompt, model="gemma3:latest"):
    payload = {
        "model": model,
        "prompt": prompt,
        "system": "You are an academic tutor, and you are meant to provide students with short concise responses. Answer concisely and directly. Limit responses to 1-2 sentences.",
        "stream": False # Keep false because the UI is made for that..Set to True if you want streaming responses, like real-time responses.
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        return f"Sorry, there was an error: {e}"

# Example usage:
# answer = ask_ollama("What is the quadratic formula?", model="llama2")