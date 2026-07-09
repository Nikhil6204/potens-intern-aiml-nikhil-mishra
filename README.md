# Document Q&A with Citations

A RAG system over 5 AI-governance policy documents, with source citations,
contradiction detection between documents, a multilingual query/answer flow,
and an explicit no-hallucination guard. Built as a 24-hour take-home;
tradeoffs and known limitations are called out honestly at the bottom rather
than glossed over.

## What's in the corpus

Five original (self-written, not scraped) markdown documents under
`data/docs/`, deliberately drafted as a coherent but *imperfect* internal
policy set for a fictional company ("Northwind Analytics"), plus a public
reference doc:

1. `doc1_eu_ai_act_overview.md` — overview of the EU AI Act's risk tiers
2. `doc2_data_privacy_ai_policy.md` — data privacy & AI policy
3. `doc3_model_risk_management_guide.md` — model risk management guide
4. `doc4_ai_incident_response_playbook.md` — AI incident response playbook
5. `doc5_vendor_ai_procurement_standard.md` — vendor AI procurement standard

**Two contradictions are baked in on purpose**, so `/contradict` has something
real to find rather than always returning "no conflict":
- Data retention: doc2 requires vendor deletion of training data **within 30
  days** of contract termination; doc5 allows vendors to retain **anonymized**
  derivatives **for up to 12 months**. (Arguably reconcilable — doc5's carve-out
  is for anonymized data only — which is exactly the kind of nuanced case a
  contradiction checker needs to reason about, not just pattern-match numbers.)
- Incident escalation timing: doc3 requires critical model incidents be
  reported to the Model Risk Committee **within 24 hours**; doc4 gives SEV-1/2
  AI safety incidents **72 hours** to escalate to Engineering Leadership/Trust
  & Safety. doc4 even acknowledges this overlap and says to default to the
  shorter window — a good test of whether the model actually reads that far.

## Architecture

```
data/docs/*.md  →  ingest/chunker.py  →  ingest/embed_store.py (Chroma)  →  chroma_db/
                                                                                │
ui/app.py (Streamlit)  ⇄  backend/main.py (FastAPI)  ⇄  backend/rag.py ──────┤
                                              ⇄  backend/contradiction.py ────┤
                                              ⇄  backend/llm_client.py (Groq/OpenAI)
```

## Chunking strategy

See the full rationale in the docstring at the top of `ingest/chunker.py`.
Short version: our docs are markdown with a clean `## heading` structure, so
we chunk **structurally first** (split on headings, so a citation can point
at "Section 3, Vendor Data Retention Requirements" rather than "chunk 14"),
then **by size second** (sections under ~800 chars stay whole; longer
sections are split with a sentence-boundary-aware recursive splitter,
target ~800 chars, ~150 char overlap, so a rule never gets sliced mid-sentence
and a straddling sentence stays retrievable from either side of a split).
Every chunk carries `doc_id`, `source`, `section`, `chunk_index`, and
character offsets into the original file.

This produced 46 chunks across the 5 documents (~9 per doc) — small enough to
stay topically coherent, large enough to carry context for the LLM.

## No-hallucination guard (the part I spent the most time on)

Four layers, described in full in `backend/rag.py`:

1. **Retrieval gate** — if the best retrieved chunk's similarity is below a
   threshold (default 0.28 cosine), we don't call the LLM at all. Weak
   context is the #1 way a RAG system ends up "helpfully" answering from the
   model's own training data instead of the documents.
2. **Prompt-level gate** — the system prompt requires the model to output
   `"covered": false` and a fixed refusal string when the context doesn't
   actually answer the question, even if it's topically related.
3. **Citation verification** — every citation is checked server-side against
   the actual retrieved chunk IDs. A hallucinated `chunk_id` is dropped, not
   trusted.
4. **Coverage/citation consistency check** — if the model claims `covered:
   true` but returns zero valid citations, we override it and return "not
   covered" anyway, because an unsupported "yes" is worse than an honest "I
   don't know."

The eval set (`backend/eval/eval_set.json`) includes one deliberately
out-of-scope question ("What is the capital of France?") specifically to
verify the refusal path works end-to-end, not just in isolated unit logic.

## Multilingual flow

Retrieval uses `paraphrase-multilingual-MiniLM-L12-v2`
(sentence-transformers), which embeds ~50 languages into a shared vector
space — so a Spanish or Hindi query retrieves the right English chunks
*before* any translation happens. `langdetect` identifies the query
language locally (no API call), and the LLM is instructed to write the final
answer in that language, grounded only in the (English) retrieved chunks.
This is the "translation step at the boundary" the assignment says is
acceptable for a 24-hour build — output is translated/generated directly in
the target language rather than running a full separate machine-translation
pipeline. Caveat: translation quality rides on the underlying LLM's
multilingual fluency, which is decent for major world languages via
Llama-3.3-70B but weaker for low-resource languages — flagged as a known
limitation below, not hidden.

## Contradiction detection

`backend/contradiction.py` doesn't dump two full documents into the LLM.
It aligns chunks across documents by embedding similarity first (find, for
each chunk in doc A, its closest chunk in doc B), keeps the top-N
topically-aligned pairs, and only asks the LLM to judge conflict *within
those specific pairs*, per pair, with reasoning. This keeps every verdict
traceable to two exact chunks instead of a vague whole-document impression.

## Stretch goals implemented

- **Confidence score + human-in-the-loop gate**: `backend/rag.py` combines
  retrieval similarity and the model's self-reported confidence into one
  score; below a threshold (default 0.55) the response is flagged
  `needs_human_review: true` and the UI shows a warning banner instead of
  presenting a shaky answer with the same visual weight as a solid one.
- **Cross-encoder reranker**: `backend/reranker.py`, opt-in via a UI checkbox
  or `use_reranker: true` in the `/ask` request. Retrieves a wider candidate
  set (3x top-k) with the bi-encoder, then reranks down to top-k with
  `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Eval set**: `backend/eval/eval_set.json` — 10 Q&A pairs with ground
  truth, 9 answerable (one per rough topic area, spread across all 5 docs)
  plus 1 deliberately out-of-scope trap question. `backend/eval/run_eval.py`
  scores retrieval@k and checks the refusal path. Runnable via `GET /eval`
  or the Streamlit "Eval" tab.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GROQ_API_KEY (free key: https://console.groq.com)

python -m ingest.ingest          # builds chroma_db/ and data/registry.json

uvicorn backend.main:app --reload --port 8000     # terminal 1
streamlit run ui/app.py                            # terminal 2
```

The first run will download the embedding model (~470MB) and, if you enable
the reranker, the cross-encoder model (~90MB) — both from Hugging Face, both
free, both cached locally after the first download.

## API quick reference

```bash
curl -X POST localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "How many days does a vendor have to delete data after contract termination?"}'

curl -X POST localhost:8000/contradict -H "Content-Type: application/json" \
  -d '{"doc_id_a": "doc2_data_privacy_ai_policy", "doc_id_b": "doc5_vendor_ai_procurement_standard"}'

curl localhost:8000/documents
curl localhost:8000/eval
```

## Honest limitations

- **Not tested against a live LLM API in this environment.** This was built
  in a sandbox without outbound network access, so I could not actually call
  Groq/OpenAI or download the embedding models to run an end-to-end pass.
  The chunker itself *was* run against the real documents (see the ingest
  logic and output in the build log) and produces clean, sensibly-sized,
  section-aware chunks. The rest of the pipeline is written carefully against
  the documented Chroma/sentence-transformers/Groq APIs but you should treat
  first-run debugging as part of the setup, not assume zero bugs.
- **Corpus is small and self-authored.** 5 documents / 46 chunks is enough to
  demonstrate the mechanics honestly but is not a stress test of retrieval at
  scale. Similarity thresholds (0.28 attempt gate, 0.55 confidence gate) were
  chosen by reasoning about the embedding model's typical cosine-similarity
  range for related vs. unrelated text, not tuned against held-out data —
  they will likely need adjustment for a different corpus or domain.
  Contradiction alignment threshold (0.15) is quite loose deliberately: recall
  over precision when hunting for pairs worth even checking, since the
  contradiction-judgment step downstream is the layer with the harder
  decision, not the alignment layer.
- **Cross-encoder reranker is English-trained.** It still runs on non-English
  candidate chunks (the candidates were already retrieved via multilingual
  embeddings), but its relevance judgments will be less reliable for
  non-English queries. Off by default for that reason.
- **Contradiction detection is bounded by embedding alignment.** If two
  documents conflict on a topic using very different vocabulary (no lexical
  or semantic overlap at all), the alignment step may not surface that pair
  for the LLM to judge. This is a recall limitation of the "align first, then
  judge" design, traded deliberately against the alternative (all-pairs
  comparison) blowing up context size on longer documents.
- **`/ask`'s JSON-mode reliance on the model.** Groq/OpenAI JSON mode is
  generally reliable but not guaranteed-valid; `llm_client.chat_json` has a
  fallback parser for markdown-fenced JSON but will raise `LLMError` (not
  silently fail) if the model still returns something unparseable. That
  surfaces as a 500 to the caller — visible, not swallowed.
- **No auth, rate limiting, or multi-tenancy.** Out of scope for a 24-hour
  functional build; would be required before any real deployment.
- **Single-writer local Chroma.** Fine for this project's scale; a real
  deployment with concurrent writers would want Chroma running as a server or
  a managed vector DB.

  ## Demo:
  [https://github.com/Nikhil6204/potens-intern-aiml-nikhil-mishra/tree/main/docs](https://github.com/Nikhil6204/potens-intern-aiml-nikhil-mishra/blob/main/docs/Screenshot%202026-07-09%20200015.png)

  https://github.com/Nikhil6204/potens-intern-aiml-nikhil-mishra/blob/main/docs/Screenshot%202026-07-09%20200015.png
