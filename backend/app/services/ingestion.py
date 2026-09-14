"""Extracción y limpieza de texto documental, y división en fragmentos (chunks)."""

import re
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_text_pdf(path: str) -> list[tuple[int, str]]:
    """Devuelve una lista de (número_de_página, texto)."""
    reader = PdfReader(path)
    return [(i, page.extract_text() or "") for i, page in enumerate(reader.pages, start=1)]


def extract_text_docx(path: str) -> str:
    doc = DocxDocument(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_txt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def needs_ocr(pages: list[tuple[int, str]]) -> bool:
    """Heurística: si la mayoría de páginas no tienen texto extraíble, es probable que el
    PDF sea escaneado y requiera OCR."""
    if not pages:
        return True
    empty = sum(1 for _, text in pages if len(text.strip()) < 20)
    return empty / len(pages) > 0.6


def run_ocr(path: str) -> list[tuple[int, str]]:
    """Punto de extensión para conectar un motor OCR (p. ej. pytesseract + pdf2image).
    No implementado en este esqueleto."""
    raise NotImplementedError(
        "OCR no está conectado todavía. Instala pytesseract/pdf2image (u otro motor) e "
        "implementa esta función para soportar PDFs escaneados."
    )


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide el texto en fragmentos por palabras con solapamiento, para conservar
    contexto suficiente entre fragmentos consecutivos."""
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(words), step):
        piece = words[start : start + chunk_size]
        if not piece:
            break
        chunks.append(" ".join(piece))
        if start + chunk_size >= len(words):
            break
    return chunks
