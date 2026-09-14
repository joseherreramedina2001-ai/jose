from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Document, DocumentChunk, IndexingStatus
from app.services import ingestion
from app.services.embeddings import get_embedding_provider


def index_document(db: Session, document: Document) -> None:
    """Extrae, limpia, divide en fragmentos, calcula embeddings y almacena los vectores
    de un documento ya subido. Marca el documento como ERROR (sin interrumpir el resto
    del sistema) si algo falla, por ejemplo un PDF escaneado que requiere OCR."""
    settings = get_settings()
    document.indexing_status = IndexingStatus.PROCESANDO
    db.commit()

    try:
        ext = Path(document.file_path).suffix.lower()

        if ext == ".pdf":
            pages = ingestion.extract_text_pdf(document.file_path)
            if ingestion.needs_ocr(pages):
                raise NotImplementedError(
                    "Este PDF parece escaneado y requiere OCR, que aún no está conectado "
                    "en este esqueleto (ver app/services/ingestion.py::run_ocr)."
                )
            raw_units: list[tuple[int | None, str]] = list(pages)
        elif ext == ".docx":
            raw_units = [(None, ingestion.extract_text_docx(document.file_path))]
        elif ext == ".txt":
            raw_units = [(None, ingestion.extract_text_txt(document.file_path))]
        else:
            raise ValueError(f"Formato no soportado todavía: {ext}")

        embedder = get_embedding_provider()
        chunk_index = 0

        for page_number, raw_text in raw_units:
            text = ingestion.clean_text(raw_text)
            if not text:
                continue
            pieces = ingestion.chunk_text(text, settings.chunk_size, settings.chunk_overlap)
            if not pieces:
                continue
            vectors = embedder.embed(pieces)
            for content, vector in zip(pieces, vectors):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk_index,
                        content=content,
                        page=page_number,
                        embedding=vector,
                    )
                )
                chunk_index += 1

        document.indexing_status = IndexingStatus.COMPLETADO
        db.commit()

    except Exception:
        document.indexing_status = IndexingStatus.ERROR
        db.commit()
        raise
