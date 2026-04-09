"""FAISS vector store for email similarity search."""
from __future__ import annotations
import json, os
from config import EMBEDDING_MODEL, FAISS_INDEX_PATH, FAISS_META_PATH

_emb = None
_idx = None
_meta: list[dict] = []

def _get_emb():
    global _emb
    if _emb is None:
        from sentence_transformers import SentenceTransformer
        _emb = SentenceTransformer(EMBEDDING_MODEL)
    return _emb

def _get_idx(dim: int = 384):
    global _idx
    if _idx is None:
        import faiss
        _idx = faiss.read_index(FAISS_INDEX_PATH) if os.path.exists(FAISS_INDEX_PATH) else faiss.IndexFlatL2(dim)
    return _idx

def _load():
    global _meta
    if not _meta and os.path.exists(FAISS_META_PATH):
        with open(FAISS_META_PATH) as f:
            _meta = json.load(f)

def _save():
    import faiss
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(_idx, FAISS_INDEX_PATH)
    with open(FAISS_META_PATH, "w") as f:
        json.dump(_meta, f, indent=2)

def add(text: str, meta: dict):
    _load()
    vec = _get_emb().encode([text], normalize_embeddings=True).astype("float32")
    _get_idx(vec.shape[1]).add(vec)
    _meta.append(meta)
    _save()

def search(text: str, top_k: int = 3) -> list[dict]:
    _load()
    if not _meta:
        return []
    vec = _get_emb().encode([text], normalize_embeddings=True).astype("float32")
    idx = _get_idx(vec.shape[1])
    k = min(top_k, idx.ntotal)
    if k == 0:
        return []
    dists, indices = idx.search(vec, k)
    results = []
    for d, i in zip(dists[0], indices[0]):
        if i < len(_meta):
            e = dict(_meta[i])
            e["similarity"] = round(float(1 - d), 3)
            results.append(e)
    return results
