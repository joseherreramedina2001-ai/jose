import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import schemas
from app.config import get_settings
from app.database import get_db
from app.models import Document, DocumentStatus
from app.services.indexing import index_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("", response_model=schemas.DocumentOut)
def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form(...),
    number: str | None = Form(None),
    year: int | None = Form(None),
    issuing_entity: str | None = Form(None),
    dependency: str | None = Form(None),
    category_id: str | None = Form(None),
    version: str | None = Form(None),
    source_url: str | None = Form(None),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Formato no soportado: {ext}. Usa PDF, DOCX o TXT.")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    document = Document(
        title=title,
        doc_type=doc_type,
        number=number,
        year=year,
        issuing_entity=issuing_entity,
        dependency=dependency,
        category_id=category_id or None,
        version=version,
        source_url=source_url,
        status=DocumentStatus.DESCONOCIDO,
        file_path="",
    )
    db.add(document)
    db.flush()  # asigna el id antes de escribir el archivo en disco

    dest = upload_dir / f"{document.id}{ext}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    document.file_path = str(dest)
    db.commit()
    db.refresh(document)

    try:
        # Nota: se indexa de forma síncrona por simplicidad. En producción, mover a una
        # cola de tareas en segundo plano (Celery/RQ/background tasks de FastAPI) para no
        # bloquear la respuesta con documentos grandes.
        index_document(db, document)
    except Exception:
        pass  # el estado de error queda registrado en document.indexing_status

    db.refresh(document)
    return document


@router.get("", response_model=list[schemas.DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.uploaded_at.desc()).all()


@router.get("/{document_id}", response_model=schemas.DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Documento no encontrado")
    return document


@router.patch("/{document_id}", response_model=schemas.DocumentOut)
def update_document(document_id: str, payload: schemas.DocumentUpdate, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Documento no encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "status" and value is not None:
            document.status = DocumentStatus(value)
        else:
            setattr(document, field, value)

    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Documento no encontrado")
    Path(document.file_path).unlink(missing_ok=True)
    db.delete(document)
    db.commit()


@router.post("/{document_id}/reindex", response_model=schemas.DocumentOut)
def reindex_document(document_id: str, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Documento no encontrado")
    for chunk in list(document.chunks):
        db.delete(chunk)
    db.commit()
    index_document(db, document)
    db.refresh(document)
    return document
