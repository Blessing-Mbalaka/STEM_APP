#This works the same way as the chatbot.py but here is the catch:
#This one uses embeddings to allow for enhanced context accuracy from the DB.
import os
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


def _list_available_models():
    try:
        resp = requests.get(OLLAMA_TAGS_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json() or {}
        models = []
        for entry in data.get("models", []):
            models.append({
                "name": entry.get("name") or entry.get("model"),
                "details": entry.get("details", {})
            })
        return models
    except Exception:
        return []


def _resolve_model(explicit: str | None, env_var: str, predicate=None, exclude=None) -> str | None:
    exclude = set(exclude or [])
    if explicit:
        explicit = explicit.strip()
        if explicit and explicit not in exclude:
            return explicit
    env_value = os.getenv(env_var)
    if env_value:
        env_value = env_value.strip()
        if env_value and env_value not in exclude:
            return env_value
    models = _list_available_models()
    if not models:
        return None
    if predicate:
        for entry in models:
            name = entry.get("name")
            if name and name not in exclude and predicate(entry):
                return name
    for entry in models:
        name = entry.get("name")
        if name and name not in exclude:
            return name
    return None


def _extract_error_message(exc):
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get("error") or data.get("message")
        except Exception:
            try:
                return response.text
            except Exception:
                return None
    return None


def ask_ollama(prompt, model=None):
    tried = set()
    chosen = _resolve_model(model, "OLLAMA_CHAT_MODEL")
    while chosen and chosen not in tried:
        tried.add(chosen)
        payload = {
            "model": chosen,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except requests.HTTPError as exc:
            error_msg = _extract_error_message(exc) or str(exc)
            lowered = (error_msg or "").lower()
            if any(keyword in lowered for keyword in ("not found", "requires more system memory")):
                chosen = _resolve_model(None, "OLLAMA_CHAT_MODEL", exclude=tried)
                continue
            return f"Sorry, there was an error: {error_msg}"
        except Exception as exc:
            return f"Sorry, there was an error: {exc}"
    if not chosen:
        return "Sorry, no Ollama models are currently available."
    return "Sorry, I couldn't find an available model to answer right now."


def get_embedding(text, model=None):
    def _is_embedding(entry):
        if not entry:
            return False
        name = (entry.get("name") or "").lower()
        families = entry.get("details", {}).get("families", []) or []
        families = [str(f).lower() for f in families if f]
        if "embed" in name or "bert" in name:
            return True
        return any("embed" in f or "bert" in f for f in families)

    tried = set()
    chosen = _resolve_model(model, "OLLAMA_EMBED_MODEL", predicate=_is_embedding)
    while chosen and chosen not in tried:
        tried.add(chosen)
        payload = {
            "model": chosen,
            "prompt": text
        }
        try:
            response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except requests.HTTPError as exc:
            error_msg = _extract_error_message(exc) or str(exc)
            lowered = (error_msg or "").lower()
            if any(keyword in lowered for keyword in ("not found", "requires more system memory")):
                chosen = _resolve_model(None, "OLLAMA_EMBED_MODEL", predicate=_is_embedding, exclude=tried)
                continue
            return []
        except Exception:
            return []
    return []


def find_similar(query, vector_db, model=None):
    # Get embedding for the query
    query_embedding = get_embedding(query, model=model)
    if not query_embedding:
        return []
    # Search vector_db for similar embeddings (vector_db should have a .search method)
    return vector_db.search(query_embedding)

# Example usage:
# answer = ask_ollama("What is the quadratic formula?", model="llama3.2:latest")
# embedding = get_embedding("What is the quadratic formula?", model="nomic-embed-text:latest")
# similar_docs = find_similar("What is the quadratic formula?", vector_db)
