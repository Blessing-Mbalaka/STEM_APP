import os
import sys
import django
import requests
import numpy as np
import json

# Set up Django
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stem_app.settings")
django.setup()

from main.views.chatbotmodel import build_index_from_resources

OLLAMA_EMBED_URL = "http://localhost:11434/v1/embeddings"
EMBED_FILE = os.path.join(PROJECT_ROOT, "media", "embeddings.npy")
META_FILE = os.path.join(PROJECT_ROOT, "media", "metadata.json")

def get_gemini_embedding(text, model_name="text-embedding-004"):
    # Placeholder for the actual Gemini embedding function
    return None

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

def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        # Fallback to binary read if PyMuPDF not available
        with open(pdf_path, "rb") as fh:
            return fh.read().decode("latin-1", errors="replace")
    except Exception:
        return ""

def build_index_from_resources(resource_dir: str, embed_model="text-embedding-004"):
    """
    Enhanced version that tracks subject folders and handles PDFs with subject tagging
    """
    files = []
    for root, _, filenames in os.walk(resource_dir):
        for fn in filenames:
            if fn.startswith("."):
                continue
            if fn.lower().endswith(('.pdf', '.txt', '.md', '.doc', '.docx')):
                full_path = os.path.join(root, fn)
                
                # Extract subject from folder path
                rel_path = os.path.relpath(root, resource_dir)
                subject = rel_path.split(os.sep)[0] if rel_path != "." else "General"
                
                files.append({
                    "path": full_path,
                    "subject": subject,
                    "filename": fn
                })

    metas = []
    embeddings = []
    
    for file_info in files:
        path = file_info["path"]
        subject = file_info["subject"]
        filename = file_info["filename"]
        
        print(f"Processing [{subject}]: {filename}")
        
        # Extract text based on file type
        if path.lower().endswith('.pdf'):
            text = extract_pdf_text(path)
        else:
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
            print(f"  ⚠️ No text extracted from {filename}")
            continue

        # Chunk large documents (important for PDFs)
        chunks = chunk_text(text, chunk_size=5000, overlap=500)
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very small chunks
                continue
                
            vec = get_embedding(chunk, model=embed_model)
            if vec is None:
                continue
                
            embeddings.append(np.array(vec, dtype=np.float32))
            metas.append({
                "path": path,
                "subject": subject,  # Add subject tag
                "title": f"{filename} (Part {i+1})",
                "snippet": chunk[:500],
                "chunk_index": i,
                "filename": filename
            })

    if not embeddings:
        print("❌ No embeddings created")
        return False

    emb_mat = np.vstack(embeddings).astype(np.float32)
    np.save(str(EMBED_FILE), emb_mat)
    with open(META_FILE, "w", encoding="utf-8") as fh:
        json.dump(metas, fh, ensure_ascii=False, indent=2)
    
    # Print summary by subject
    subject_counts = {}
    for meta in metas:
        subject = meta["subject"]
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    
    print(f"\n✅ Indexed {len(embeddings)} chunks from {len(files)} files")
    print("📊 By Subject:")
    for subject, count in sorted(subject_counts.items()):
        print(f"   {subject}: {count} chunks")
    
    return True

def chunk_text(text, chunk_size=5000, overlap=500):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to end at a sentence boundary
        if end < text_len:
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            boundary = max(last_period, last_newline)
            if boundary > start + chunk_size * 0.8:  # If boundary is reasonable
                chunk = text[start:start + boundary + 1]
                end = start + boundary + 1
        
        chunks.append(chunk.strip())
        start = end - overlap  # Overlap for continuity
        
        if start >= text_len:
            break
    
    return chunks

def main():
    # Point to your knowledge base folder
    resource_dir = os.path.join(PROJECT_ROOT, "media", "course_resources")
    
    print(f"Building knowledge base from: {resource_dir}")
    print("This will process all PDFs and text files in the folder...")
    
    success = build_index_from_resources(resource_dir)
    
    if success:
        print("✅ Knowledge base built successfully!")
        print("Your chatbot can now answer questions based on the uploaded documents.")
    else:
        print("❌ Failed to build knowledge base. Check if files exist in the folder.")

if __name__ == "__main__":
    main()