"""
Stretch goal: cross-encoder reranker.

Bi-encoder retrieval (what embed_store.py does) embeds the query and each
chunk independently, which is fast and scales, but it can miss fine-grained
relevance because the query and chunk never actually attend to each other.
A cross-encoder reads (query, chunk) pairs together and scores relevance
directly, which is slower (must be run per-candidate at query time) but more
accurate - so the standard pattern is: bi-encoder retrieves a wider candidate
set (e.g. top 15), cross-encoder reranks down to the top-k we actually show
the LLM.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2 - small, free, local, well-suited
to short passage reranking. It's English-trained; for non-English queries we
still rerank (embeddings already did the cross-lingual matching to build the
candidate set), but the reranker's signal is weaker outside English. This is
called out in the README as a known limitation rather than hidden.
"""
from typing import List, Dict, Any

from sentence_transformers import CrossEncoder

_reranker = None
RERANK_CANDIDATE_MULTIPLIER = 3
MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(MODEL_NAME)
    return _reranker


def rerank(query: str, candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    if not candidates:
        return candidates
    model = _get_reranker()
    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs)
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
    candidates.sort(key=lambda c: -c["rerank_score"])
    return candidates[:top_k]
