import pytest

from backend.documents.extractor import validate_file, UnsupportedFormatError, _extract_txt, EmptyDocumentError
import tempfile
import os


def test_validate_file_rechaza_extension_no_permitida():
    with pytest.raises(UnsupportedFormatError):
        validate_file("archivo.exe", 100, (".pdf", ".docx", ".txt"), 50)


def test_validate_file_rechaza_tamano_excesivo():
    with pytest.raises(ValueError):
        validate_file("archivo.pdf", 200 * 1024 * 1024, (".pdf", ".docx", ".txt"), 50)


def test_validate_file_acepta_archivo_valido():
    validate_file("circular.pdf", 1024, (".pdf", ".docx", ".txt"), 50)  # no debe lanzar


def test_extract_txt_vacio_lanza_error():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("   ")
        path = f.name
    try:
        with pytest.raises(EmptyDocumentError):
            _extract_txt(path)
    finally:
        os.remove(path)


def test_extract_txt_con_contenido():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Circular institucional de prueba.")
        path = f.name
    try:
        result = _extract_txt(path)
        assert result.paginas[0].texto == "Circular institucional de prueba."
        assert result.requirio_ocr is False
    finally:
        os.remove(path)
