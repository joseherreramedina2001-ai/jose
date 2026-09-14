"""
Recuperación de fragmentos relevantes para una consulta.

Implementa:
- Búsqueda semántica vía vector store.
- Priorización de documentos vigentes sobre derogados/reemplazados.
- Cálculo de nivel de confianza (alta/media/baja) según similitud (sección 13).
- Detección simple de posible contradicción entre documentos distintos
  recuperados para la misma consulta (sección 6).
"""
from dataclasses import dataclass
from typing import List

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.embeddings.provider import get_embedding_provider
from backend.rag.vector_store import get_vector_store
from backend.models.models import DocumentChunk, Document, VigenciaEnum


@dataclass
class RetrievedFragment:
    chunk: DocumentChunk
    documento: Document
    score: float


@dataclass
class RetrievalResult:
    fragmentos: List[RetrievedFragment]
    nivel_confianza: str  # "alta" | "media" | "baja" | "ninguna"
    posible_contradiccion: bool
    suficiente: bool  # si hay base suficiente para generar una respuesta normativa


# Bonus/penalización aplicada al score por estado de vigencia, para que un
# documento "vigente" gane frente a uno "derogado" con similitud parecida,
# sin que esto oculte el derogado si es lo único relevante encontrado.
_VIGENCIA_WEIGHT = {
    VigenciaEnum.vigente: 0.05,
    VigenciaEnum.modificado: 0.0,
    VigenciaEnum.en_revision: 0.0,
    VigenciaEnum.desconocido: -0.02,
    VigenciaEnum.reemplazado: -0.08,
    VigenciaEnum.derogado: -0.12,
}


def retrieve(db: Session, pregunta: str, top_k: int | None = None) -> RetrievalResult:
    top_k = top_k or settings.RETRIEVAL_TOP_K

    embedder = get_embedding_provider()
    store = get_vector_store()

    query_vector = embedder.embed_texts([pregunta])[0]
    raw_hits = store.search(query_vector, top_k=top_k * 2)  # sobre-recuperar para poder re-priorizar

    fragmentos: List[RetrievedFragment] = []
    for vector_ref, score in raw_hits:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.vector_ref == vector_ref).first()
        if not chunk:
            continue
        documento = db.query(Document).filter(Document.id == chunk.document_id).first()
        if not documento:
            continue
        ajustado = score + _VIGENCIA_WEIGHT.get(documento.estado_vigencia, 0.0)
        fragmentos.append(RetrievedFragment(chunk=chunk, documento=documento, score=ajustado))

    fragmentos.sort(key=lambda f: f.score, reverse=True)
    fragmentos = fragmentos[:top_k]

    if not fragmentos:
        return RetrievalResult(fragmentos=[], nivel_confianza="ninguna", posible_contradiccion=False, suficiente=False)

    mejor_score = fragmentos[0].score
    nivel = _nivel_confianza(mejor_score)
    suficiente = mejor_score >= settings.MIN_SIMILARITY_THRESHOLD

    posible_contradiccion = _detectar_contradiccion(fragmentos)

    return RetrievalResult(
        fragmentos=fragmentos,
        nivel_confianza=nivel,
        posible_contradiccion=posible_contradiccion,
        suficiente=suficiente,
    )


def _nivel_confianza(score: float) -> str:
    if score >= 0.65:
        return "alta"
    elif score >= settings.MIN_SIMILARITY_THRESHOLD:
        return "media"
    return "baja"


def _detectar_contradiccion(fragmentos: List[RetrievedFragment]) -> bool:
    """Heurística MVP: si entre los fragmentos de mayor score hay documentos
    distintos sobre el mismo tema con estados de vigencia distintos y ambos
    con score alto, se marca como posible contradicción para que el sistema
    lo exponga en vez de decidir arbitrariamente (sección 6). Un sistema más
    maduro usaría un segundo paso de NLI (entailment/contradiction) con el LLM."""
    if len(fragmentos) < 2:
        return False

    top = fragmentos[:3]
    temas = {f.documento.tema for f in top if f.documento.tema}
    vigencias = {f.documento.estado_vigencia for f in top}
    documentos_distintos = len({f.documento.id for f in top}) > 1

    mismo_tema_vigencias_distintas = (
        documentos_distintos and len(temas) <= 1 and len(vigencias) > 1
    )
    return mismo_tema_vigencias_distintas
