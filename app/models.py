from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    source_url: HttpUrl | None = None


class DocumentOut(BaseModel):
    id: int
    title: str
    source_url: str | None = None
    created_at: datetime
    chunk_count: int


class DemoLoadResponse(BaseModel):
    added: int
    skipped: int
    total_documents: int
    sample_questions: list[str]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1200)
    top_k: int = Field(default=6, ge=1, le=12)


class Citation(BaseModel):
    id: str
    title: str
    source_url: str | None = None
    snippet: str
    score: float


class SafetyReport(BaseModel):
    blocked: bool = False
    reasons: list[str] = Field(default_factory=list)


class ClaimCheck(BaseModel):
    claim: str
    supported: bool
    citation_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class JudgeReport(BaseModel):
    score: float
    verdict: str
    details: dict[str, Any] = Field(default_factory=dict)


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    safety: SafetyReport
    claims: list[ClaimCheck]
    hallucination_risk: str
    judge: JudgeReport
    trace: list[str]
