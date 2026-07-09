"""
/contradict pipeline.

Given two document IDs, we don't just dump both full documents into the LLM
and ask "do these conflict?" - for longer documents that wastes context and
buries the model in irrelevant sections that were never going to conflict
(e.g. comparing an incident-response playbook's communication section
against a privacy policy's breach-definition section tells us nothing).

Instead we align the two documents at the chunk level:
  1. Embed every chunk of doc A and doc B (already done at ingest time).
  2. For each chunk in doc A, find its most similar chunk(s) in doc B.
     High similarity here means "these two chunks are talking about the same
     topic" - which is a *necessary* precondition for a contradiction (you
     can't conflict on a topic you don't both address).
  3. Keep the top-N most topically-aligned cross-document pairs.
  4. Hand only those pairs to the LLM and ask it to judge, per pair, whether
     the two chunks state something incompatible, with reasoning - rather
     than a vague global "yes/no" over two whole documents.
  5. Aggregate into an overall verdict.

This keeps the LLM's job narrow and checkable: for every claimed conflict we
can point at the exact two chunks (and their source files) that produced it.
"""
import json
import os
from typing import Dict, Any, List

from ingest.embed_store import get_collection
from backend.llm_client import chat_json, LLMError

REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "registry.json"
)

TOP_N_PAIRS = int(os.getenv("CONTRADICTION_TOP_N_PAIRS", "6"))
MIN_ALIGNMENT_SIMILARITY = float(os.getenv("MIN_ALIGNMENT_SIMILARITY", "0.15"))

_collection = None


def _collection_singleton():
    global _collection
    if _collection is None:
        _collection = get_collection(reset=False)
    return _collection


def _load_registry() -> Dict[str, Any]:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_doc_chunks(collection, doc_id: str) -> List[Dict[str, Any]]:
    result = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    chunks = []
    for cid, doc, meta in zip(result["ids"], result["documents"], result["metadatas"]):
        chunks.append({"chunk_id": cid, "text": doc, **meta})
    chunks.sort(key=lambda c: c["chunk_index"])
    return chunks


def _align_chunks(collection, chunks_a: List[Dict], doc_id_b: str, top_n: int) -> List[Dict]:
    """For each chunk in doc A, query the collection restricted to doc B and
    keep the best match. Return the globally top-N pairs by similarity."""
    pairs = []
    for ca in chunks_a:
        res = collection.query(
            query_texts=[ca["text"]],
            n_results=1,
            where={"doc_id": doc_id_b},
        )
        if not res["ids"][0]:
            continue
        similarity = 1 - res["distances"][0][0]
        if similarity < MIN_ALIGNMENT_SIMILARITY:
            continue
        cb_meta = res["metadatas"][0][0]
        cb_text = res["documents"][0][0]
        cb_id = res["ids"][0][0]
        pairs.append(
            {
                "similarity": round(float(similarity), 4),
                "chunk_a": ca,
                "chunk_b": {"chunk_id": cb_id, "text": cb_text, **cb_meta},
            }
        )
    pairs.sort(key=lambda p: -p["similarity"])
    return pairs[:top_n]


SYSTEM_PROMPT = """You are a compliance analyst comparing paired excerpts from two \
policy/guide documents that were flagged as discussing the same topic. For EACH \
pair, decide whether the two excerpts state something that actually conflicts \
(a reader following both documents could not comply with both simultaneously, or \
they state different facts/numbers/rules about the same specific point). Do NOT \
flag pairs as conflicting just because they discuss the same topic with different \
emphasis, or because one is more detailed than the other - that is not a conflict.

For each pair output whether it conflicts, the specific topic, and concise \
reasoning citing the specific detail from each side that conflicts (e.g. "Doc A \
requires deletion within 30 days; Doc B allows retention up to 12 months").

Respond ONLY with JSON of this exact shape, no markdown fences:
{
  "pair_results": [
    {
      "pair_index": integer,
      "conflicts": boolean,
      "topic": string,
      "reasoning": string
    }
  ],
  "overall_conflicts": boolean,
  "overall_summary": string
}
"""


def compare_documents(doc_id_a: str, doc_id_b: str) -> Dict[str, Any]:
    registry = _load_registry()
    if doc_id_a not in registry or doc_id_b not in registry:
        return {
            "error": f"Unknown doc_id(s). Known doc_ids: {sorted(registry.keys())}"
        }
    if doc_id_a == doc_id_b:
        return {"error": "doc_id_a and doc_id_b must be different documents."}

    collection = _collection_singleton()
    chunks_a = _get_doc_chunks(collection, doc_id_a)
    pairs = _align_chunks(collection, chunks_a, doc_id_b, TOP_N_PAIRS)

    if not pairs:
        return {
            "doc_id_a": doc_id_a,
            "doc_id_b": doc_id_b,
            "contradicts": False,
            "summary": "No topically-aligned sections were found between these two "
                        "documents, so no contradiction could be assessed.",
            "evidence": [],
        }

    pair_blocks = []
    for i, p in enumerate(pairs):
        pair_blocks.append(
            f"PAIR {i}:\n"
            f"  Doc A ({p['chunk_a']['source']}, section \"{p['chunk_a']['section']}\", "
            f"chunk {p['chunk_a']['chunk_id']}): {p['chunk_a']['text']}\n"
            f"  Doc B ({p['chunk_b']['source']}, section \"{p['chunk_b']['section']}\", "
            f"chunk {p['chunk_b']['chunk_id']}): {p['chunk_b']['text']}\n"
        )
    user = "\n---\n".join(pair_blocks)

    try:
        result = chat_json(SYSTEM_PROMPT, user, temperature=0.0)
    except LLMError as e:
        return {"error": str(e)}

    evidence = []
    any_conflict = False
    for pr in result.get("pair_results", []):
        idx = pr.get("pair_index")
        if idx is None or idx >= len(pairs):
            continue
        p = pairs[idx]
        conflicts = bool(pr.get("conflicts", False))
        any_conflict = any_conflict or conflicts
        evidence.append(
            {
                "conflicts": conflicts,
                "topic": pr.get("topic", ""),
                "reasoning": pr.get("reasoning", ""),
                "alignment_similarity": p["similarity"],
                "doc_a_snippet": {
                    "source": p["chunk_a"]["source"],
                    "section": p["chunk_a"]["section"],
                    "chunk_id": p["chunk_a"]["chunk_id"],
                    "text": p["chunk_a"]["text"],
                },
                "doc_b_snippet": {
                    "source": p["chunk_b"]["source"],
                    "section": p["chunk_b"]["section"],
                    "chunk_id": p["chunk_b"]["chunk_id"],
                    "text": p["chunk_b"]["text"],
                },
            }
        )

    return {
        "doc_id_a": doc_id_a,
        "doc_id_b": doc_id_b,
        "contradicts": bool(result.get("overall_conflicts", any_conflict)),
        "summary": result.get("overall_summary", ""),
        "evidence": evidence,
    }
