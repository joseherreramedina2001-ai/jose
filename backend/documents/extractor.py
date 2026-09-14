"""
Extracción de texto por página/párrafo, conservando la referencia de página
(fundamental para poder citar la fuente con precisión, sección 5 y 20).
"""
from dataclasses import dataclass
from typing import List
import os


@dataclass
class ExtractedPage:
    numero_pagina: int
    texto: str


@dataclass
class ExtractionResult:
    paginas: List[ExtractedPage]
    requirio_ocr: bool


class UnsupportedFormatError(Exception):
    pass


class EmptyDocumentError(Exception):
    pass


def extract_text(filepath: str, formato: str) -> ExtractionResult:
    formato = formato.lower()
    if formato == "pdf":
        return _extract_pdf(filepath)
    elif formato == "docx":
        return _extract_docx(filepath)
    elif formato == "txt":
        return _extract_txt(filepath)
    else:
        raise UnsupportedFormatError(f"Formato no soportado: {formato}")


def _extract_pdf(filepath: str) -> ExtractionResult:
    import pypdf

    reader = pypdf.PdfReader(filepath)
    paginas = []
    total_chars = 0
    for i, page in enumerate(reader.pages, start=1):
        texto = (page.extract_text() or "").strip()
        total_chars += len(texto)
        paginas.append(ExtractedPage(numero_pagina=i, texto=texto))

    # Heurística: si casi no hay texto seleccionable, se asume PDF escaneado -> OCR
    avg_chars_per_page = total_chars / max(len(paginas), 1)
    requirio_ocr = avg_chars_per_page < 20

    if requirio_ocr:
        paginas = _ocr_pdf(filepath)

    if not any(p.texto.strip() for p in paginas):
        raise EmptyDocumentError("El documento no contiene texto extraíble, ni siquiera vía OCR.")

    return ExtractionResult(paginas=paginas, requirio_ocr=requirio_ocr)


def _ocr_pdf(filepath: str) -> List[ExtractedPage]:
    """OCR página por página. Requiere pytesseract + pdf2image + poppler/tesseract
    instalados en el sistema (ver README > Instalación > OCR)."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as e:
        raise RuntimeError(
            "OCR_ENABLED=True pero faltan dependencias de OCR (pytesseract/pdf2image/tesseract-ocr). "
            "Ver README sección OCR."
        ) from e

    images = convert_from_path(filepath)
    paginas = []
    for i, img in enumerate(images, start=1):
        texto = pytesseract.image_to_string(img, lang="spa")
        paginas.append(ExtractedPage(numero_pagina=i, texto=texto.strip()))
    return paginas


def _extract_docx(filepath: str) -> ExtractionResult:
    import docx

    doc = docx.Document(filepath)
    texto_completo = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if not texto_completo.strip():
        raise EmptyDocumentError("El documento DOCX no contiene texto.")
    # DOCX no tiene "páginas" reales sin renderizar; se trata como página única
    # y el chunker se encarga de dividirlo en fragmentos manejables.
    return ExtractionResult(paginas=[ExtractedPage(numero_pagina=1, texto=texto_completo)], requirio_ocr=False)


def _extract_txt(filepath: str) -> ExtractionResult:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        texto = f.read()
    if not texto.strip():
        raise EmptyDocumentError("El archivo TXT está vacío.")
    return ExtractionResult(paginas=[ExtractedPage(numero_pagina=1, texto=texto)], requirio_ocr=False)


def validate_file(filename: str, size_bytes: int, allowed_extensions: tuple, max_size_mb: int):
    """Validaciones de seguridad antes de procesar (sección 15)."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise UnsupportedFormatError(f"Extensión no permitida: {ext}. Permitidas: {allowed_extensions}")
    if size_bytes > max_size_mb * 1024 * 1024:
        raise ValueError(f"El archivo supera el tamaño máximo permitido ({max_size_mb} MB).")
