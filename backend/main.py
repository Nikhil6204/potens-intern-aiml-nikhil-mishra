"""
FastAPI backend.

Run with:
    uvicorn backend.main:app --reload --port 8000

Endpoints:
    GET  /health
    GET  /documents        - list ingested documents
    POST /ask               - RAG question answering with citations
    POST /contradict        - conflict detection between two documents
    GET  /eval               - run the retrieval@k eval set and return scores
"""
import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import AskRequest, AskResponse, ContradictRequest, DocumentInfo
from backend.rag import answer_question
from backend.contradiction import compare_documents

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "registry.json")

app = FastAPI(title="Document Q&A with Citations", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents", response_model=list[DocumentInfo])
def list_documents():
    if not os.path.exists(REGISTRY_PATH):
        raise HTTPException(
            status_code=500,
            detail="No registry found. Run `python -m ingest.ingest` first.",
        )
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)
    return [
        DocumentInfo(doc_id=doc_id, source=v["source"], title=v["title"], num_chunks=v["num_chunks"])
        for doc_id, v in sorted(registry.items())
    ]


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        result = answer_question(req.question, k=req.top_k, use_reranker=req.use_reranker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    result.pop("retrieved_chunks", None)  # internal debug detail, not part of the public contract
    return result


@app.post("/contradict")
def contradict(req: ContradictRequest):
    result = compare_documents(req.doc_id_a, req.doc_id_b)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/eval")
def run_eval():
    from backend.eval.run_eval import run
    return run()
