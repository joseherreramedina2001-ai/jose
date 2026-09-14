"""
Divide el texto extraído en fragmentos (chunks) manteniendo:
- Contexto suficiente (solapamiento entre chunks).
- Trazabilidad hacia el documento y la página de origen (sección 20).

Usamos un split aproximado por palabras (proxy simple de tokens) en vez de
depender de un tokenizer de un proveedor específico, para mantener la capa
de IA desacoplada (sección 23).
"""
import re
from dataclasses import dataclass
from typing import List

from backend.documents.extractor import ExtractedPage


@dataclass
class Chunk:
    chunk_id: str
    texto: str
    pagina: int
    orden: int
    articulo: str | None = None
    numeral: str | None = None
    apartado: str | None = None


_ARTICULO_RE = re.compile(r"(art[íi]culo\s+\d+[a-záéíóú]*)", re.IGNORECASE)
_NUMERAL_RE = re.compile(r"(\b\d+(\.\d+)+\b)")


def _detectar_estructura(texto: str) -> tuple[str | None, str | None]:
    """Heurística simple para detectar referencias a artículo/numeral dentro
    del propio fragmento, para enriquecer la cita (sección 5). No inventa
    nada: si no encuentra patrón, deja el campo vacío."""
    art = _ARTICULO_RE.search(texto)
    num = _NUMERAL_RE.search(texto)
    return (art.group(1) if art else None, num.group(1) if num else None)


def chunk_document(
    doc_code: str,
    paginas: List[ExtractedPage],
    chunk_size_words: int = 350,
    overlap_words: int = 60,
) -> List[Chunk]:
    chunks: List[Chunk] = []
    orden = 0

    for pagina in paginas:
        palabras = pagina.texto.split()
        if not palabras:
            continue

        start = 0
        chunk_num_en_pagina = 0
        while start < len(palabras):
            end = min(start + chunk_size_words, len(palabras))
            fragmento = " ".join(palabras[start:end])
            chunk_num_en_pagina += 1
            orden += 1

            articulo, numeral = _detectar_estructura(fragmento)
            chunk_id = f"{doc_code}-P{pagina.numero_pagina:02d}-C{chunk_num_en_pagina:02d}"

            chunks.append(Chunk(
                chunk_id=chunk_id,
                texto=fragmento,
                pagina=pagina.numero_pagina,
                orden=orden,
                articulo=articulo,
                numeral=numeral,
            ))

            if end == len(palabras):
                break
            start = end - overlap_words  # solapamiento

    return chunks
