import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import User, QueryLog
from backend.auth.security import get_current_user
from backend.api.schemas import ChatQueryRequest, ChatQueryResponse, FuenteOut, RatingRequest
from backend.rag.generator import responder_pregunta

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryResponse)
def query(payload: ChatQueryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not payload.pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")

    inicio = time.perf_counter()
    resultado = responder_pregunta(db, payload.pregunta)
    duracion_ms = int((time.perf_counter() - inicio) * 1000)

    log = QueryLog(
        user_id=current_user.id,
        pregunta=payload.pregunta,
        respuesta=resultado.texto,
        respondido=resultado.respondido,
        nivel_confianza=resultado.nivel_confianza,
        chunks_recuperados=resultado.chunk_ids_usados,
        modelo_utilizado=resultado.modelo_utilizado,
        tiempo_respuesta_ms=duracion_ms,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return ChatQueryResponse(
        respondido=resultado.respondido,
        respuesta=resultado.texto,
        fuentes=[FuenteOut(**vars(f)) for f in resultado.fuentes],
        nivel_confianza=resultado.nivel_confianza,
        posible_contradiccion=resultado.posible_contradiccion,
        query_log_id=log.id,
    )


@router.get("/history")
def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = (
        db.query(QueryLog)
        .filter(QueryLog.user_id == current_user.id)
        .order_by(QueryLog.creado_en.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": l.id,
            "pregunta": l.pregunta,
            "respuesta": l.respuesta,
            "respondido": l.respondido,
            "creado_en": l.creado_en,
        }
        for l in logs
    ]


@router.post("/{query_log_id}/rating")
def rate(query_log_id: str, payload: RatingRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = db.query(QueryLog).filter(QueryLog.id == query_log_id, QueryLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if not (1 <= payload.valoracion <= 5):
        raise HTTPException(status_code=400, detail="La valoración debe estar entre 1 y 5")
    log.valoracion = payload.valoracion
    db.commit()
    return {"detail": "Valoración registrada"}
