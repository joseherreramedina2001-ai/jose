from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import ConfidenceLevel, Document, IndexingStatus, Interaction

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=schemas.StatsOut)
def stats(db: Session = Depends(get_db)):
    total_documents = db.query(func.count(Document.id)).scalar() or 0
    documents_indexed = (
        db.query(func.count(Document.id))
        .filter(Document.indexing_status == IndexingStatus.COMPLETADO)
        .scalar()
        or 0
    )
    documents_pending = (
        db.query(func.count(Document.id))
        .filter(Document.indexing_status.in_([IndexingStatus.PENDIENTE, IndexingStatus.PROCESANDO]))
        .scalar()
        or 0
    )
    total_queries = db.query(func.count(Interaction.id)).scalar() or 0
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    queries_today = (
        db.query(func.count(Interaction.id)).filter(Interaction.created_at >= today_start).scalar() or 0
    )
    unanswered = (
        db.query(func.count(Interaction.id))
        .filter(Interaction.confidence == ConfidenceLevel.NO_DISPONIBLE)
        .scalar()
        or 0
    )
    avg_time = db.query(func.avg(Interaction.response_time_ms)).scalar() or 0.0
    avg_rating = db.query(func.avg(Interaction.rating)).scalar()

    return {
        "total_documents": total_documents,
        "documents_indexed": documents_indexed,
        "documents_pending": documents_pending,
        "total_queries": total_queries,
        "queries_today": queries_today,
        "unanswered_queries": unanswered,
        "avg_response_time_ms": float(avg_time),
        "avg_rating": float(avg_rating) if avg_rating is not None else None,
    }


@router.get("/audit", response_model=list[schemas.InteractionOut])
def audit_log(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Interaction).order_by(Interaction.created_at.desc()).limit(limit).all()
