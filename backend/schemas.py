from typing import List, Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question in any language")
    top_k: Optional[int] = Field(default=5, ge=1, le=15)
    use_reranker: Optional[bool] = Field(default=False)


class Citation(BaseModel):
    chunk_id: str
    source: str
    section: str
    snippet: str


class AskResponse(BaseModel):
    question: str
    answer: Optional[str]
    covered: Optional[bool]
    confidence: float
    needs_human_review: bool
    citations: List[Citation]
    language: dict
    note: Optional[str] = None
    error: Optional[str] = None


class ContradictRequest(BaseModel):
    doc_id_a: str
    doc_id_b: str


class DocumentInfo(BaseModel):
    doc_id: str
    source: str
    title: str
    num_chunks: int
