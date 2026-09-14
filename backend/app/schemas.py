from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class QueryRequest(BaseModel):
    question: str
    user_id: str | None = None


class SourceOut(BaseModel):
    document_id: str
    document_title: str
    doc_type: str
    number: str | None = None
    year: int | None = None
    issue_date: date | None = None
    status: str
    page: int | None = None
    article: str | None = None
    numeral: str | None = None
    section: str | None = None
    source_url: str | None = None
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    confidence: str
    sources: list[SourceOut]
    warning: str | None = None
    interaction_id: str


class FeedbackIn(BaseModel):
    rating: int


class CategoryIn(BaseModel):
    name: str
    description: str | None = None


class CategoryOut(CategoryIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    doc_type: str
    number: str | None
    issue_date: date | None
    year: int | None
    issuing_entity: str | None
    dependency: str | None
    category_id: str | None
    version: str | None
    status: str
    source_url: str | None
    indexing_status: str
    source: str
    uploaded_at: datetime
    updated_at: datetime


class DocumentUpdate(BaseModel):
    title: str | None = None
    doc_type: str | None = None
    number: str | None = None
    issue_date: date | None = None
    year: int | None = None
    issuing_entity: str | None = None
    dependency: str | None = None
    category_id: str | None = None
    version: str | None = None
    status: str | None = None
    source_url: str | None = None


class StatsOut(BaseModel):
    total_documents: int
    documents_indexed: int
    documents_pending: int
    total_queries: int
    queries_today: int
    unanswered_queries: int
    avg_response_time_ms: float
    avg_rating: float | None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question: str
    answer: str
    confidence: str
    model_used: str
    response_time_ms: int
    rating: int | None
    created_at: datetime
