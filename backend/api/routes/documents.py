import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.config import settings
from backend.models.models import Document, User, RoleEnum, VigenciaEnum
from backend.auth.security import require_role, get_current_user
from backend.api.schemas import DocumentOut, DocumentUpdateMetadata
from backend.documents.extractor import validate_file, UnsupportedFormatError
from backend.services.document_processor import process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    nombre: str = Form(...),
    tipo_documento: str = Form(None),
    numero: str = Form(None),
    anio: int = Form(None),
    entidad_emisora: str = Form(None),
    dependencia: str = Form(None),
    tema: str = Form(None),
    version: str = Form(None),
    estado_vigencia: str = Form("desconocido"),
    url_original: str = Form(None),
    es_demo: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin, RoleEnum.funcionario)),
):
    contenido = await file.read()
    try:
        validate_file(file.filename, len(contenido), settings.ALLOWED_EXTENSIONS, settings.MAX_UPLOAD_SIZE_MB)
    except (UnsupportedFormatError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    ruta = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")
    with open(ruta, "wb") as f:
        f.write(contenido)

    doc = Document(
        nombre=nombre,
        tipo_documento=tipo_documento,
        numero=numero,
        anio=anio,
        entidad_emisora=entidad_emisora,
        dependencia=dependencia,
        tema=tema,
        version=version,
        estado_vigencia=VigenciaEnum(estado_vigencia),
        url_original=url_original,
        ruta_archivo=ruta,
        formato=ext,
        es_demo=es_demo,
        subido_por_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document, db, doc.id)

    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Document).order_by(Document.fecha_carga.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if os.path.exists(doc.ruta_archivo):
        os.remove(doc.ruta_archivo)
    db.delete(doc)  # cascada elimina también sus chunks
    db.commit()
    return {"detail": "Documento eliminado. Nota: en backend faiss_local sus vectores "
                       "quedan huérfanos en el índice hasta una reconstrucción manual; "
                       "ver README > Limitaciones conocidas."}


@router.post("/{document_id}/process", response_model=DocumentOut)
def reprocess_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin, RoleEnum.funcionario)),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    process_document(db, document_id)
    db.refresh(doc)
    return doc


@router.patch("/{document_id}/metadata", response_model=DocumentOut)
def update_metadata(
    document_id: str,
    payload: DocumentUpdateMetadata,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if payload.tema is not None:
        doc.tema = payload.tema
    if payload.estado_vigencia is not None:
        doc.estado_vigencia = VigenciaEnum(payload.estado_vigencia)
    if payload.version is not None:
        doc.version = payload.version
    if payload.reemplazado_por_id is not None:
        doc.reemplazado_por_id = payload.reemplazado_por_id
    db.commit()
    db.refresh(doc)
    return doc
