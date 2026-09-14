"""
Orquesta: retrieval -> construcción de prompt con fragmentos -> LLM -> respuesta.

Este módulo es el punto único donde se decide si el sistema responde con
contenido normativo o con un mensaje de "información insuficiente"
(sección 2, principio fundamental). Ninguna otra parte del sistema debe
saltarse este guardrail.
"""
from dataclasses import dataclass, field
from typing import List

from sqlalchemy.orm import Session

from backend.rag.retriever import retrieve, RetrievalResult, RetrievedFragment
from backend.rag.llm_provider import get_llm_provider
from backend.rag.system_prompt import SYSTEM_PROMPT

MENSAJE_SIN_INFORMACION = (
    "No encontré información suficiente en la documentación institucional disponible "
    "para responder esta consulta con seguridad. Te recomiendo verificar la normativa "
    "vigente o remitir la consulta al área competente."
)

MENSAJE_BAJA_COINCIDENCIA = (
    "No se encontraron fuentes suficientemente relacionadas con tu consulta."
)


@dataclass
class FuenteCitada:
    documento_nombre: str
    tipo_documento: str | None
    numero: str | None
    anio: int | None
    estado_vigencia: str
    pagina: int | None
    apartado: str | None
    articulo: str | None
    chunk_id: str
    url_original: str | None


@dataclass
class RespuestaGenerada:
    respondido: bool
    texto: str
    fuentes: List[FuenteCitada] = field(default_factory=list)
    nivel_confianza: str = "ninguna"
    posible_contradiccion: bool = False
    chunk_ids_usados: List[str] = field(default_factory=list)
    modelo_utilizado: str | None = None


def responder_pregunta(db: Session, pregunta: str) -> RespuestaGenerada:
    resultado: RetrievalResult = retrieve(db, pregunta)

    # Guardrail 1: no hay fragmentos en absoluto.
    if not resultado.fragmentos:
        return RespuestaGenerada(respondido=False, texto=MENSAJE_SIN_INFORMACION, nivel_confianza="ninguna")

    # Guardrail 2: la similitud es demasiado baja para confiar en el resultado (sección 13).
    if not resultado.suficiente:
        return RespuestaGenerada(
            respondido=False,
            texto=MENSAJE_BAJA_COINCIDENCIA,
            nivel_confianza=resultado.nivel_confianza,
        )

    fuentes = [_a_fuente(f) for f in resultado.fragmentos]
    contexto = _construir_contexto(resultado.fragmentos)

    user_prompt = (
        f"Pregunta del usuario:\n{pregunta}\n\n"
        f"Fragmentos institucionales recuperados (usa únicamente esta información):\n\n{contexto}"
    )
    if resultado.posible_contradiccion:
        user_prompt += (
            "\n\nADVERTENCIA: los fragmentos recuperados provienen de documentos con "
            "estados de vigencia distintos sobre un tema similar. Señala esta situación "
            "explícitamente en tu respuesta en vez de elegir arbitrariamente una disposición."
        )

    llm = get_llm_provider()
    texto_generado = llm.generate(SYSTEM_PROMPT, user_prompt)

    return RespuestaGenerada(
        respondido=True,
        texto=texto_generado,
        fuentes=fuentes,
        nivel_confianza=resultado.nivel_confianza,
        posible_contradiccion=resultado.posible_contradiccion,
        chunk_ids_usados=[f.chunk.chunk_id for f in resultado.fragmentos],
        modelo_utilizado=getattr(llm, "_model", type(llm).__name__),
    )


def _construir_contexto(fragmentos: List[RetrievedFragment]) -> str:
    partes = []
    for f in fragmentos:
        d = f.documento
        c = f.chunk
        encabezado = (
            f"[FUENTE chunk_id={c.chunk_id} | documento={d.nombre} "
            f"({d.tipo_documento or 's/d'} {d.numero or ''} de {d.anio or 's/f'}) | "
            f"vigencia={d.estado_vigencia.value} | pagina={c.pagina or 's/d'} | "
            f"apartado={c.apartado or c.articulo or c.numeral or 's/d'}]"
        )
        partes.append(f"{encabezado}\n{c.texto}")
    return "\n\n---\n\n".join(partes)


def _a_fuente(f: RetrievedFragment) -> FuenteCitada:
    d, c = f.documento, f.chunk
    return FuenteCitada(
        documento_nombre=d.nombre,
        tipo_documento=d.tipo_documento,
        numero=d.numero,
        anio=d.anio,
        estado_vigencia=d.estado_vigencia.value,
        pagina=c.pagina,
        apartado=c.apartado,
        articulo=c.articulo,
        chunk_id=c.chunk_id,
        url_original=d.url_original,
    )
