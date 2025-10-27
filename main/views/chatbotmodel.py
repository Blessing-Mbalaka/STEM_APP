#This works the same way as the chatbot.py but here is the catch:
#This one uses embeddings to allow for enhanced context accuracy from the DB.
import os
import requests
import json
import numpy as np
from pathlib import Path

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EMBED_FILE = DATA_DIR / "resources_embeddings.npy"
META_FILE = DATA_DIR / "resources_meta.json"

# Import Gemini functions
from .gemini import ask_gemini, get_gemini_embedding

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

# Update embedding function to use Gemini by default
def get_embedding(text, model="text-embedding-004"):
    """Use Gemini for embeddings by default, fallback to Ollama if needed"""
    embedding = get_gemini_embedding(text, model_name=model)
    if embedding is not None:
        return embedding
    
    # Fallback to Ollama if Gemini fails
    try:
        payload = {"model": "nomic-embed-text:latest", "input": text}
        resp = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "embedding" in data:
            return np.array(data["embedding"], dtype=np.float32)
    except Exception:
        pass
    return None

def build_prompt_with_context(user_question: str, top_docs: list):
    context_parts = []
    for i, doc in enumerate(top_docs, 1):
        meta = doc['meta']
        context_parts.append(f"Document {i} ({meta.get('title')}):\n{meta.get('snippet', '')}\n")
    
    context = "\n\n".join(context_parts)
    prompt = (
        "Use the following course resources as context to answer the user's question. "
        "Cite the document titles when helpful and answer clearly and concisely.\n\n"
        f"Context:\n{context}\n\nUser question:\n{user_question}\n\n"
        "Answer (use ONLY the context; if the answer is not present in the context, "
        "reply exactly: \"I don't know based on the provided materials.\"):")
    return prompt

def answer_with_rag(user_question: str,
                    k=3,
                    embed_model="text-embedding-004",
                    llm_model="gemini-2.5-flash",  # Change from gemini-1.5-flash-latest
                    confidence_threshold=0.45,
                    fallback_to_llm=False):
    """
    RAG function using Gemini 2.5 Flash for both embeddings and LLM response.
    """
    top = query_index(user_question, k=k, embed_model=embed_model)
    if not top:
        if fallback_to_llm:
            return ask_gemini(user_question, model_name=llm_model)
        return "I don't know based on the available course materials."

    max_score = max(r.get("score", 0.0) for r in top)
    if max_score < confidence_threshold:
        if fallback_to_llm:
            system = ("Answer the question but note if you're not certain. "
                     "Start with: 'Based on general knowledge (not course materials):'")
            return ask_gemini(user_question, model_name=llm_model, system_prompt=system)
        return "I don't know based on the available course materials."

    prompt = build_prompt_with_context(user_question, top)
    system = ("Use ONLY the provided course materials to answer questions. "
             "If the answer isn't in the context, say: 'I don't know based on the provided materials.'")
    return ask_gemini(prompt, model_name=llm_model, system_prompt=system)

def build_index_from_resources(resource_dir: str, embed_model="text-embedding-004"):
    """
    Walk resource_dir, extract text, embed each file using Gemini embeddings
    and persist embeddings + metadata for later querying.
    """
    files = []
    for root, _, filenames in os.walk(resource_dir):
        for fn in filenames:
            if fn.startswith("."):
                continue
            files.append(os.path.join(root, fn))

    metas = []
    embeddings = []
    for path in files:
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("latin-1", errors="replace")
        except Exception:
            text = ""

        if not text.strip():
            continue
        chunk = text if len(text) < 20000 else text[:20000]
        vec = get_embedding(chunk, model=embed_model)
        if vec is None:
            continue
        embeddings.append(np.array(vec, dtype=np.float32))
        metas.append({"path": path, "title": os.path.basename(path), "snippet": chunk[:500]})

    if not embeddings:
        return False

    emb_mat = np.vstack(embeddings).astype(np.float32)
    np.save(str(EMBED_FILE), emb_mat)
    with open(META_FILE, "w", encoding="utf-8") as fh:
        json.dump(metas, fh, ensure_ascii=False, indent=2)
    return True

def load_index():
    if not EMBED_FILE.exists() or not META_FILE.exists():
        return None, None
    emb = np.load(str(EMBED_FILE))
    with open(META_FILE, "r", encoding="utf-8") as fh:
        metas = json.load(fh)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    emb_norm = emb / norms
    return emb_norm, metas

def query_index(query: str, k=3, embed_model="text-embedding-004"):
    emb_norm, metas = load_index()
    if emb_norm is None:
        return []
    qvec = get_embedding(query, model=embed_model)
    if qvec is None:
        return []
    q = np.array(qvec, dtype=np.float32)
    qnorm = q / (np.linalg.norm(q) or 1.0)
    sims = np.dot(emb_norm, qnorm)
    top_idx = np.argsort(-sims)[:k]
    results = []
    for idx in top_idx:
        results.append({"score": float(sims[idx]), "meta": metas[idx]})
    return results

def find_similar(query, vector_db, model="text-embedding-004"):
    # Get embedding for the query
    query_embedding = get_embedding(query, model=model)
    if not query_embedding:
        return []
    # Search vector_db for similar embeddings (vector_db should have a .search method)
    return vector_db.search(query_embedding)

# Example usage:
# answer = answer_with_rag("What is the quadratic formula?")  # Uses Gemini 2.5 Flash
# embedding = get_embedding("What is the quadratic formula?")  # Uses Gemini text-embedding-004
