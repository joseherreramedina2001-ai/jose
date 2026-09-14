from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.models import Document, QueryLog, User, RoleEnum, ProcessingStatusEnum
from backend.auth.security import require_role
from backend.api.schemas import StatisticsOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/statistics", response_model=StatisticsOut)
def statistics(db: Session = Depends(get_db), current_user: User = Depends(require_role(RoleEnum.admin))):
    total_docs = db.query(func.count(Document.id)).scalar()
    procesados = db.query(func.count(Document.id)).filter(
        Document.estado_procesamiento == ProcessingStatusEnum.procesado
    ).scalar()
    pendientes = db.query(func.count(Document.id)).filter(
        Document.estado_procesamiento.in_([ProcessingStatusEnum.pendiente, ProcessingStatusEnum.procesando])
    ).scalar()
    con_error = db.query(func.count(Document.id)).filter(
        Document.estado_procesamiento == ProcessingStatusEnum.error
    ).scalar()

    total_consultas = db.query(func.count(QueryLog.id)).scalar()
    sin_respuesta = db.query(func.count(QueryLog.id)).filter(QueryLog.respondido == False).scalar()  # noqa: E712
    tiempo_promedio = db.query(func.avg(QueryLog.tiempo_respuesta_ms)).scalar()

    return StatisticsOut(
        total_documentos=total_docs or 0,
        documentos_procesados=procesados or 0,
        documentos_pendientes=pendientes or 0,
        documentos_error=con_error or 0,
        total_consultas=total_consultas or 0,
        consultas_sin_respuesta=sin_respuesta or 0,
        tiempo_promedio_respuesta_ms=float(tiempo_promedio) if tiempo_promedio else None,
    )


@router.get("/audit")
def audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
    limit: int = 100,
):
    logs = db.query(QueryLog).order_by(QueryLog.creado_en.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "usuario_id": l.user_id,
            "fecha": l.creado_en,
            "pregunta": l.pregunta,
            "chunks_recuperados": l.chunks_recuperados,
            "respondido": l.respondido,
            "nivel_confianza": l.nivel_confianza,
            "modelo_utilizado": l.modelo_utilizado,
            "tiempo_respuesta_ms": l.tiempo_respuesta_ms,
        }
        for l in logs
    ]
