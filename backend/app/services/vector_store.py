from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk


def similarity_search(db: Session, query_embedding: list[float], top_k: int):
    """Devuelve (chunk, documento, distancia_coseno) ordenados por cercanía."""
    stmt = (
        select(
            DocumentChunk,
            Document,
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(Document, DocumentChunk.document_id == Document.id)
        .order_by("distance")
        .limit(top_k)
    )
    return db.execute(stmt).all()
