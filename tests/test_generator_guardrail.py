"""
Estas pruebas verifican la sección 2 (principio fundamental) y la sección 25
del prompt: el sistema NUNCA debe generar una respuesta normativa sin
fragmentos de respaldo, y debe declarar explícitamente cuándo no tiene
información suficiente.
"""
from unittest.mock import patch

from backend.rag.generator import (
    responder_pregunta,
    MENSAJE_SIN_INFORMACION,
    MENSAJE_BAJA_COINCIDENCIA,
)
from backend.rag.retriever import RetrievalResult, RetrievedFragment
from backend.models.models import Document, DocumentChunk, VigenciaEnum


def _doc_y_chunk(vigencia=VigenciaEnum.vigente, tema="convivencia escolar"):
    doc = Document(
        id="doc-1", nombre="Circular 015 de 2026", tipo_documento="circular", numero="015",
        anio=2026, tema=tema, estado_vigencia=vigencia, ruta_archivo="x.pdf", formato="pdf",
    )
    chunk = DocumentChunk(
        id="chunk-1", chunk_id="RES-2026-0015-P08-C03", document_id="doc-1",
        texto="Texto normativo de ejemplo sobre el procedimiento.", pagina=8,
        apartado="4.2", orden=1,
    )
    return doc, chunk


def test_sin_fragmentos_no_inventa_respuesta(db):
    with patch("backend.rag.generator.retrieve") as mock_retrieve:
        mock_retrieve.return_value = RetrievalResult(
            fragmentos=[], nivel_confianza="ninguna", posible_contradiccion=False, suficiente=False
        )
        resultado = responder_pregunta(db, "¿Qué dice la normativa sobre algo no documentado?")

    assert resultado.respondido is False
    assert resultado.texto == MENSAJE_SIN_INFORMACION
    assert resultado.fuentes == []


def test_baja_coincidencia_no_genera_respuesta_normativa(db):
    doc, chunk = _doc_y_chunk()
    with patch("backend.rag.generator.retrieve") as mock_retrieve:
        mock_retrieve.return_value = RetrievalResult(
            fragmentos=[RetrievedFragment(chunk=chunk, documento=doc, score=0.1)],
            nivel_confianza="baja",
            posible_contradiccion=False,
            suficiente=False,  # por debajo del umbral
        )
        resultado = responder_pregunta(db, "pregunta poco relacionada")

    assert resultado.respondido is False
    assert resultado.texto == MENSAJE_BAJA_COINCIDENCIA


def test_con_fragmentos_suficientes_genera_respuesta_con_fuentes(db):
    doc, chunk = _doc_y_chunk()
    with patch("backend.rag.generator.retrieve") as mock_retrieve:
        mock_retrieve.return_value = RetrievalResult(
            fragmentos=[RetrievedFragment(chunk=chunk, documento=doc, score=0.8)],
            nivel_confianza="alta",
            posible_contradiccion=False,
            suficiente=True,
        )
        resultado = responder_pregunta(db, "¿Qué procedimiento debe seguirse?")

    assert resultado.respondido is True
    assert len(resultado.fuentes) == 1
    assert resultado.fuentes[0].chunk_id == "RES-2026-0015-P08-C03"
    assert resultado.fuentes[0].documento_nombre == "Circular 015 de 2026"
    assert "RES-2026-0015-P08-C03" in resultado.chunk_ids_usados


def test_contradiccion_se_senala_en_el_prompt_al_llm(db):
    doc, chunk = _doc_y_chunk()
    with patch("backend.rag.generator.retrieve") as mock_retrieve, \
         patch("backend.rag.generator.get_llm_provider") as mock_llm:
        mock_retrieve.return_value = RetrievalResult(
            fragmentos=[RetrievedFragment(chunk=chunk, documento=doc, score=0.8)],
            nivel_confianza="alta",
            posible_contradiccion=True,
            suficiente=True,
        )
        mock_provider = mock_llm.return_value
        mock_provider.generate.return_value = "respuesta simulada"

        responder_pregunta(db, "¿Cuál es la disposición vigente?")

        user_prompt_enviado = mock_provider.generate.call_args[0][1]
        assert "ADVERTENCIA" in user_prompt_enviado
        assert "estados de vigencia distintos" in user_prompt_enviado


def test_nunca_responde_sin_pasar_por_retrieve(db):
    """Verifica que responder_pregunta siempre consulta retrieve(); si esto
    se elimina alguna vez por error, esta prueba debe fallar."""
    with patch("backend.rag.generator.retrieve") as mock_retrieve:
        mock_retrieve.return_value = RetrievalResult(
            fragmentos=[], nivel_confianza="ninguna", posible_contradiccion=False, suficiente=False
        )
        responder_pregunta(db, "cualquier pregunta")
        assert mock_retrieve.called
