from backend.rag.chunking import chunk_document
from backend.documents.extractor import ExtractedPage


def test_chunking_genera_chunk_ids_trazables():
    paginas = [ExtractedPage(numero_pagina=1, texto=" ".join(["palabra"] * 800))]
    chunks = chunk_document("RES-2026-0015", paginas, chunk_size_words=350, overlap_words=60)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.chunk_id.startswith("RES-2026-0015-P01-C")
        assert c.pagina == 1


def test_chunking_respeta_solapamiento():
    paginas = [ExtractedPage(numero_pagina=1, texto=" ".join(f"w{i}" for i in range(700)))]
    chunks = chunk_document("DOC-1", paginas, chunk_size_words=300, overlap_words=50)

    primer_chunk_palabras = chunks[0].texto.split()
    segundo_chunk_palabras = chunks[1].texto.split()
    # la región de solapamiento (últimas `overlap_words` del primer chunk)
    # debe reaparecer al inicio del segundo chunk
    overlap_esperado = primer_chunk_palabras[-50:]
    assert segundo_chunk_palabras[:50] == overlap_esperado


def test_chunking_pagina_vacia_no_genera_chunks():
    paginas = [ExtractedPage(numero_pagina=1, texto="   ")]
    chunks = chunk_document("DOC-1", paginas)
    assert chunks == []
