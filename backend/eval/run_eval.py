"""
Runs the eval set and reports:
  - retrieval@k: for each question with a known expected_doc_id, did a chunk
    from that doc appear in the top-k retrieved chunks?
  - refusal correctness: for the one question with no expected_doc_id (the
    "capital of France" out-of-scope trap), did the system correctly say
    "not covered" instead of hallucinating an answer from parametric
    knowledge?

Run standalone:
    python -m backend.eval.run_eval

Or via API:
    GET /eval
"""
import json
import os

from backend.rag import retrieve, answer_question

EVAL_SET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_set.json")


def run(k: int = 5):
    with open(EVAL_SET_PATH, "r", encoding="utf-8") as f:
        eval_set = json.load(f)

    results = []
    hits = 0
    scored = 0
    refusal_correct = None

    for item in eval_set:
        question = item["question"]
        expected_doc_id = item["expected_doc_id"]

        retrieved = retrieve(question, k=k)
        retrieved_doc_ids = [c["doc_id"] for c in retrieved]

        if expected_doc_id is not None:
            scored += 1
            hit = expected_doc_id in retrieved_doc_ids
            hits += int(hit)
            results.append(
                {
                    "id": item["id"],
                    "question": question,
                    "expected_doc_id": expected_doc_id,
                    "retrieved_doc_ids": retrieved_doc_ids,
                    "hit_at_k": hit,
                }
            )
        else:
            # out-of-scope trap question: check the full pipeline refuses correctly
            answer = answer_question(question, k=k)
            refusal_correct = (answer["covered"] is False)
            results.append(
                {
                    "id": item["id"],
                    "question": question,
                    "expected_doc_id": None,
                    "is_out_of_scope_trap": True,
                    "system_said_not_covered": refusal_correct,
                    "system_answer": answer["answer"],
                }
            )

    retrieval_at_k_score = round(hits / scored, 3) if scored else None

    return {
        "k": k,
        "num_questions": len(eval_set),
        "retrieval_at_k": retrieval_at_k_score,
        "retrieval_hits": hits,
        "retrieval_scored_questions": scored,
        "out_of_scope_refusal_correct": refusal_correct,
        "details": results,
    }


if __name__ == "__main__":
    out = run()
    print(json.dumps(out, indent=2))
