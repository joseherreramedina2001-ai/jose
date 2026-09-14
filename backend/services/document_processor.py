import re
import unicodedata
from sqlalchemy.orm import Session

from backend.models.models import Document, DocumentChunk, ProcessingStatusEnum
from backend.documents.extractor import extract_text, EmptyDocumentError, UnsupportedFormatError
from backend.rag.chunking import chunk_document
from backend.embeddings.provider import get_embedding_provider
from backend.rag.vector_store import get_vector_store


def _codigo_documento(doc: Document) -> str:
    """Código corto y legible para prefijar los chunk_id, p.ej RES-2026-0015."""
    base = f"{doc.tipo_documento or 'DOC'}-{doc.anio or 's-f'}-{doc.numero or doc.id[:6]}"
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9\-]", "", base).upper()


def process_document(db: Session, document_id: str) -> None:
    """Ejecuta el pipeline completo de un documento ya cargado: extracción,
    chunking, embeddings e indexación. Actualiza el estado de procesamiento
    para que sea visible en el panel administrativo (sección 10)."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError(f"Documento no encontrado: {document_id}")

    doc.estado_procesamiento = ProcessingStatusEnum.procesando
    db.commit()

    try:
        extraction = extract_text(doc.ruta_archivo, doc.formato)
        doc.requirio_ocr = extraction.requirio_ocr

        codigo = _codigo_documento(doc)
        chunks = chunk_document(codigo, extraction.paginas)

        if not chunks:
            raise EmptyDocumentError("No se generaron fragmentos a partir del documento.")

        embedder = get_embedding_provider()
        vectores = embedder.embed_texts([c.texto for c in chunks])

        # Se insertan primero las filas de chunks (sin embedding) y se
        # confirma la transacción, porque PgVectorStore.add() actualiza por
        # chunk_id filas ya existentes en document_chunks. FaissLocalStore no
        # depende de este orden, pero se mantiene único para ambos backends.
        for c in chunks:
            db.add(DocumentChunk(
                chunk_id=c.chunk_id,
                document_id=doc.id,
                texto=c.texto,
                pagina=c.pagina,
                articulo=c.articulo,
                numeral=c.numeral,
                apartado=c.apartado,
                orden=c.orden,
                vector_ref=c.chunk_id,
            ))
        db.commit()

        store = get_vector_store(dim=embedder.dimension())
        vector_refs = [c.chunk_id for c in chunks]
        store.add(vector_refs, vectores, document_id=doc.id)

        doc.estado_procesamiento = ProcessingStatusEnum.procesado
        doc.error_procesamiento = None
        db.commit()

    except (EmptyDocumentError, UnsupportedFormatError) as e:
        doc.estado_procesamiento = ProcessingStatusEnum.error
        doc.error_procesamiento = str(e)
        db.commit()
    except Exception as e:  # noqa: BLE001 - se registra cualquier fallo para el admin, no se oculta
        doc.estado_procesamiento = ProcessingStatusEnum.error
        doc.error_procesamiento = f"Error inesperado durante el procesamiento: {e}"
        db.commit()
        raise
