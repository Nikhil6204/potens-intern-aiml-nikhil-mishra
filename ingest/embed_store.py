"""
Embedding + vector store layer.

Embedding model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Why this model specifically: it's free, runs locally (no API key, no per-call
cost), and - critically for the multilingual requirement - it maps semantically
similar sentences from ~50 languages into the same embedding space. Our source
documents are all in English, but a query in, say, Spanish or Hindi will still
land close to the relevant English chunks in vector space. That's what lets us
retrieve correctly *before* any translation happens, rather than relying on
translation alone to bridge the language gap.

Vector store: Chroma, running in local persistent mode (no separate server to
stand up - it's a single `chromadb.PersistentClient` pointed at a folder on
disk). Good fit for a 5-document, single-machine project like this one; would
swap for a managed pgvector/Chroma-server deployment if this needed to scale
to many concurrent users or a much larger corpus.
"""
import os
from typing import List, Dict, Any

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer

PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
COLLECTION_NAME = "docs"
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


class MultilingualEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model = _get_model()
        vectors = model.encode(list(input), normalize_embeddings=True)
        return vectors.tolist()


def get_client():
    return chromadb.PersistentClient(path=PERSIST_DIR)


def get_collection(reset: bool = False):
    client = get_client()
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=MultilingualEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(collection, chunks: List) -> None:
    if not chunks:
        return
    collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "doc_id": c.doc_id,
                "source": c.source,
                "section": c.section,
                "chunk_index": c.chunk_index,
                "char_start": c.char_start,
                "char_end": c.char_end,
            }
            for c in chunks
        ],
    )


def query(collection, text: str, k: int = 5, where: Dict[str, Any] = None):
    results = collection.query(
        query_texts=[text],
        n_results=k,
        where=where,
    )
    out = []
    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]
    for i in range(len(ids)):
        # cosine distance -> similarity (0..1, higher is better)
        similarity = 1 - dists[i]
        out.append(
            {
                "chunk_id": ids[i],
                "text": docs[i],
                "similarity": round(float(similarity), 4),
                **metas[i],
            }
        )
    return out
