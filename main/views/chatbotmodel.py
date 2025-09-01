
#This works the same way as the chatbot.py but here is the catch:
#This one uses embeddings to allow for enhanced context accuracy from the DB.
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"  # Example endpoint for embeddings

def ask_ollama(prompt, model="llama2"):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        return f"Sorry, there was an error: {e}"

def get_embedding(text, model="nomic-embed-text"):
    payload = {
        "model": model,
        "prompt": text
    }
    try:
        response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("embedding", [])
    except Exception as e:
        return []

def find_similar(query, vector_db, model="nomic-embed-text"):
    # Get embedding for the query
    query_embedding = get_embedding(query, model=model)
    if not query_embedding:
        return []
    # Search vector_db for similar embeddings (vector_db should have a .search method)
    return vector_db.search(query_embedding)

# Example usage:
# answer = ask_ollama("What is the quadratic formula?", model="llama2")
# embedding = get_embedding("What is the quadratic formula?", model="nomic-embed-text")
# similar_docs = find_similar("What is the quadratic formula?", vector_db)