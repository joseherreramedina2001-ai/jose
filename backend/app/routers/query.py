from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Interaction
from app.services.rag_pipeline import run_query

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=schemas.QueryResponse)
def query(payload: schemas.QueryRequest, db: Session = Depends(get_db)):
    result = run_query(db, payload.question, payload.user_id)
    return {
        "answer": result["answer"],
        "confidence": result["confidence"],
        "warning": result["warning"],
        "interaction_id": result["interaction_id"],
        "sources": [
            {
                "document_id": s["document_id"],
                "document_title": s["document_title"],
                "doc_type": s["doc_type"],
                "number": s["number"],
                "year": s["year"],
                "issue_date": s["issue_date"],
                "status": s["status"],
                "page": s["page"],
                "article": s["article"],
                "numeral": s["numeral"],
                "section": s["section"],
                "source_url": s["source_url"],
                "excerpt": s["content"][:400],
            }
            for s in result["sources"]
        ],
    }


@router.post("/query/{interaction_id}/feedback")
def feedback(interaction_id: str, payload: schemas.FeedbackIn, db: Session = Depends(get_db)):
    interaction = db.get(Interaction, interaction_id)
    if interaction:
        interaction.rating = payload.rating
        db.commit()
    return {"ok": True}
