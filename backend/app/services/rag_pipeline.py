"""Orquesta el flujo RAG completo: normaliza la pregunta, recupera fragmentos relevantes,
prioriza documentos vigentes, detecta posibles conflictos entre fuentes, genera la
respuesta y registra la interacción para auditoría."""

import time

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ConfidenceLevel, DocumentStatus, Interaction
from app.services.embeddings import get_embedding_provider
from app.services.llm_provider import NO_INFO_MESSAGE, get_llm_provider
from app.services.vector_store import similarity_search

NON_CURRENT_STATUSES = (DocumentStatus.DEROGADO, DocumentStatus.REEMPLAZADO)


def _normalize(question: str) -> str:
    return " ".join(question.strip().split())


def run_query(db: Session, question: str, user_id: str | None = None) -> dict:
    settings = get_settings()
    started = time.perf_counter()

    normalized = _normalize(question)
    embedder = get_embedding_provider()
    [query_embedding] = embedder.embed([normalized])

    results = similarity_search(db, query_embedding, settings.top_k)

    # pgvector cosine_distance: 0 = idéntico, 2 = opuesto -> se convierte a un score de similitud.
    relevant = [
        (chunk, document, 1 - distance)
        for chunk, document, distance in results
        if (1 - distance) >= settings.similarity_threshold
    ]

    warning = None
    confidence = ConfidenceLevel.NO_DISPONIBLE
    context_chunks: list[dict] = []

    if relevant:
        confidence = ConfidenceLevel.ENCONTRADA

        statuses = {document.status for _, document, _ in relevant}
        if statuses & set(NON_CURRENT_STATUSES):
            non_current_titles = sorted(
                {d.title for _, d, _ in relevant if d.status in NON_CURRENT_STATUSES}
            )
            warning = (
                "Parte de la información recuperada proviene de documentos marcados como "
                f"derogados o reemplazados ({', '.join(non_current_titles)}). Prioriza la "
                "normativa vigente antes de actuar."
            )

        distinct_docs = {document.id for _, document, _ in relevant}
        if len(distinct_docs) > 1 and len(statuses) > 1 and warning is None:
            warning = (
                "Se encontraron disposiciones en más de un documento con distinto estado "
                "de vigencia. La respuesta requiere verificar cuál disposición se "
                "encuentra actualmente vigente."
            )

        context_chunks = [
            {
                "chunk_id": chunk.id,
                "document_id": document.id,
                "document_title": document.title,
                "doc_type": document.doc_type,
                "number": document.number,
                "year": document.year,
                "issue_date": document.issue_date,
                "status": document.status.value,
                "page": chunk.page,
                "article": chunk.article,
                "numeral": chunk.numeral,
                "section": chunk.section,
                "source_url": document.source_url,
                "content": chunk.content,
                "score": round(score, 4),
            }
            for chunk, document, score in relevant
        ]

    llm = get_llm_provider()
    answer = llm.generate(normalized, context_chunks) if context_chunks else NO_INFO_MESSAGE

    elapsed_ms = int((time.perf_counter() - started) * 1000)

    interaction = Interaction(
        user_id=user_id,
        question=question,
        answer=answer,
        confidence=confidence,
        retrieved_chunk_ids=[c["chunk_id"] for c in context_chunks],
        model_used=llm.name,
        response_time_ms=elapsed_ms,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return {
        "answer": answer,
        "confidence": confidence.value,
        "warning": warning,
        "sources": context_chunks,
        "interaction_id": interaction.id,
    }
