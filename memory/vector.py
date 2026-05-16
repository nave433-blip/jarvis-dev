import faiss
import numpy as np
import os
import pickle
import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_URL = f"{OLLAMA_HOST}/api/embeddings"
MODEL = os.getenv("JARVIS_MODEL", "llama3") # Or "nomic-embed-text" for better results
_index = None
_store = []
DB_PATH = "memory_store.pkl"
INDEX_PATH = "memory.index"

def _get_embedding(text):
    try:
        r = requests.post(OLLAMA_EMBED_URL, json={
            "model": MODEL,
            "prompt": text
        })
        r.raise_for_status()
        return r.json()["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def _get_index(dim=4096): # Llama3 default embedding dim is 4096
    global _index, _store
    if _index is None:
        if os.path.exists(INDEX_PATH):
            _index = faiss.read_index(INDEX_PATH)
            if os.path.exists(DB_PATH):
                with open(DB_PATH, "rb") as f:
                    _store = pickle.load(f)
        else:
            _index = faiss.IndexFlatL2(dim)
    return _index

def add(text):
    emb = _get_embedding(text)
    if emb is None: return
    
    index = _get_index(dim=len(emb))
    index.add(np.array([emb]).astype("float32"))
    _store.append(text)
    
    # Save
    faiss.write_index(index, INDEX_PATH)
    with open(DB_PATH, "wb") as f:
        pickle.dump(_store, f)

def search(q, k=5):
    emb = _get_embedding(q)
    if emb is None: return []
    
    index = _get_index(dim=len(emb))
    if index.ntotal == 0:
        return []
        
    D, I = index.search(np.array([emb]).astype("float32"), k)
    return [_store[i] for i in I[0] if i < len(_store)]
