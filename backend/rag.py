"""
Core /ask pipeline.

Anti-hallucination design (the part we care most about getting right):

1. RETRIEVAL GATE: we retrieve top-k chunks and look at the best similarity
   score. If even the best match is below MIN_SIMILARITY_TO_ATTEMPT, we don't
   bother calling the LLM at all - we return "not covered" directly. This
   protects against the failure mode where the LLM, given weak/irrelevant
   context, "helpfully" answers from its own parametric knowledge instead of
   the documents. No context worth reasoning over -> no LLM call -> no
   opportunity to hallucinate.

2. PROMPT-LEVEL GATE: when we do call the LLM, the system prompt requires it
   to set "covered": false and leave "answer" as a fixed refusal string if
   the retrieved chunks don't actually answer the question. This catches the
   case where retrieval returns *topically* related chunks that don't
   actually contain the answer (e.g. asking about a number that isn't in the
   passage).

3. CITATION-FORCING: every claim in the answer must be backed by a citation
   pointing at one of the retrieved chunk_ids we handed the model. We only
   accept citations whose chunk_id was actually in the retrieved set (server-
   side check) - if the model invents a chunk_id, we drop that citation
   rather than trust it blindly.

4. CONFIDENCE + HUMAN-IN-THE-LOOP GATE (stretch goal): we combine the
   retrieval similarity with the model's self-reported confidence into a
   single score. Below CONFIDENCE_REVIEW_THRESHOLD we set
   "needs_human_review": true so the UI can flag it, rather than presenting
   a shaky answer with the same visual weight as a solid one.
"""
import os
from typing import List, Dict, Any

from ingest.embed_store import get_collection, query as vector_query
from backend.llm_client import chat_json, LLMError
from backend.lang import detect_language

MIN_SIMILARITY_TO_ATTEMPT = float(os.getenv("MIN_SIMILARITY_TO_ATTEMPT", "0.28"))
TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
CONFIDENCE_REVIEW_THRESHOLD = float(os.getenv("CONFIDENCE_REVIEW_THRESHOLD", "0.55"))

NOT_COVERED_TEXT = "The documents do not contain information to answer this question."

_collection = None


def _collection_singleton():
    global _collection
    if _collection is None:
        _collection = get_collection(reset=False)
    return _collection


# NOTE: this is a plain, UNFORMATTED template. It intentionally still
# contains {not_covered}, {answer_language}, and double-braced {{ }} JSON
# example syntax. Do NOT call .format() on this at module load time -
# .format() consumes the {{ }} escaping the moment it runs, so a second
# .format() call later (e.g. to inject answer_language) would see literal
# single braces around "covered" etc. and raise a KeyError trying to treat
# them as format fields. Only ever call .format() on this ONCE, at the
# point of use in answer_question(), with BOTH not_covered and
# answer_language supplied together.
SYSTEM_PROMPT = """You are a strict document Q&A assistant. You answer ONLY using the \
CONTEXT chunks provided below. You must never use outside knowledge, even if you \
are confident it is correct.

Rules:
1. If the CONTEXT does not contain enough information to answer the question, you \
MUST set "covered" to false and set "answer" to exactly: "{not_covered}" \
(translated into the answer_language if it is not English). Do not guess, do not \
partially answer, do not fill gaps with general knowledge.
2. If the CONTEXT does answer the question, set "covered" to true and write the \
answer using ONLY facts present in the CONTEXT.
3. Every factual sentence in "answer" must be traceable to at least one chunk_id \
from the CONTEXT. List the chunk_ids you relied on in "citations", each with the \
exact "snippet" (a short verbatim excerpt, under 25 words, copied from that chunk) \
that supports the claim.
4. Do not cite a chunk_id that is not in the CONTEXT.
5. Write the "answer" field in {answer_language}, regardless of what language the \
CONTEXT is in. If the context is in English and answer_language is not English, \
translate your grounded answer into answer_language - but do not introduce facts \
that translation "helpfully" adds.
6. Provide a "confidence" float between 0 and 1 reflecting how directly and \
completely the CONTEXT answers the question (1.0 = explicit, complete, unambiguous \
answer; 0.5 = partial or indirectly inferred; low = tenuous).

Respond ONLY with a JSON object of this exact shape, no markdown fences, no prose \
outside the JSON:
{{
  "covered": boolean,
  "answer": string,
  "confidence": number,
  "citations": [
    {{"chunk_id": string, "source": string, "section": string, "snippet": string}}
  ]
}}
"""


def _build_context_block(chunks: List[Dict[str, Any]]) -> str:
    parts = []
    for c in chunks:
        parts.append(
            f"[chunk_id: {c['chunk_id']} | source: {c['source']} | section: {c['section']}]\n"
            f"{c['text']}\n"
        )
    return "\n---\n".join(parts)


def retrieve(question: str, k: int = TOP_K, use_reranker: bool = False) -> List[Dict[str, Any]]:
    collection = _collection_singleton()
    if use_reranker:
        from backend.reranker import rerank, RERANK_CANDIDATE_MULTIPLIER
        candidates = vector_query(collection, question, k=k * RERANK_CANDIDATE_MULTIPLIER)
        return rerank(question, candidates, top_k=k)
    return vector_query(collection, question, k=k)


def answer_question(question: str, k: int = TOP_K, use_reranker: bool = False) -> Dict[str, Any]:
    lang = detect_language(question)
    retrieved = retrieve(question, k=k, use_reranker=use_reranker)

    best_similarity = max((c["similarity"] for c in retrieved), default=0.0)

    if not retrieved or best_similarity < MIN_SIMILARITY_TO_ATTEMPT:
        return {
            "question": question,
            "answer": NOT_COVERED_TEXT,
            "covered": False,
            "confidence": 0.0,
            "needs_human_review": False,
            "citations": [],
            "retrieved_chunks": retrieved,
            "language": lang,
            "note": "Retrieval gate: best chunk similarity "
                    f"({best_similarity:.2f}) was below the attempt threshold "
                    f"({MIN_SIMILARITY_TO_ATTEMPT}), so the LLM was not called.",
        }

    context_block = _build_context_block(retrieved)
    # Single .format() call, both placeholders supplied together - this is
    # the only place this template is ever formatted.
    system = SYSTEM_PROMPT.format(not_covered=NOT_COVERED_TEXT, answer_language=lang["name"])
    user = f"CONTEXT:\n{context_block}\n\nQUESTION:\n{question}"

    try:
        result = chat_json(system, user, temperature=0.0)
    except LLMError as e:
        return {
            "question": question,
            "answer": None,
            "covered": None,
            "confidence": 0.0,
            "needs_human_review": True,
            "citations": [],
            "retrieved_chunks": retrieved,
            "language": lang,
            "error": str(e),
        }

    # Server-side validation: only accept citations pointing at chunks we
    # actually retrieved. Never trust the model's citation list blindly.
    retrieved_ids = {c["chunk_id"]: c for c in retrieved}
    valid_citations = []
    for cit in result.get("citations", []):
        cid = cit.get("chunk_id")
        if cid in retrieved_ids:
            valid_citations.append(
                {
                    "chunk_id": cid,
                    "source": retrieved_ids[cid]["source"],
                    "section": retrieved_ids[cid]["section"],
                    "snippet": cit.get("snippet", "")[:400],
                }
            )

    model_confidence = float(result.get("confidence", 0.5) or 0.0)
    combined_confidence = round((model_confidence + best_similarity) / 2, 3)
    covered = bool(result.get("covered", False))

    # If the model claims coverage but produced zero valid citations, treat
    # this as untrustworthy rather than presenting an unsupported answer.
    if covered and not valid_citations:
        return {
            "question": question,
            "answer": NOT_COVERED_TEXT,
            "covered": False,
            "confidence": 0.0,
            "needs_human_review": True,
            "citations": [],
            "retrieved_chunks": retrieved,
            "language": lang,
            "note": "Model claimed coverage but returned no verifiable citations; "
                    "answer was suppressed as a safety measure.",
        }

    return {
        "question": question,
        "answer": result.get("answer", NOT_COVERED_TEXT),
        "covered": covered,
        "confidence": combined_confidence,
        "needs_human_review": covered and combined_confidence < CONFIDENCE_REVIEW_THRESHOLD,
        "citations": valid_citations,
        "retrieved_chunks": retrieved,
        "language": lang,
    }