"""
Modelos ORM.

Nota sobre vectores: si VECTOR_BACKEND=pgvector, la columna `embedding` de
DocumentChunk se define con el tipo Vector de pgvector (ver migración en
database/migrations). En modo faiss_local, los embeddings NO se guardan en
esta tabla: se guardan en un índice FAISS aparte y aquí solo se conserva
`vector_ref` (el id que los vincula). Esto permite cambiar de backend sin
tocar el resto del código (ver rag/vector_store.py).
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, ForeignKey, Enum, Float, JSON
)
from sqlalchemy.orm import relationship

from backend.database.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    admin = "admin"
    funcionario = "funcionario"
    consulta = "consulta"


class VigenciaEnum(str, enum.Enum):
    vigente = "vigente"
    derogado = "derogado"
    reemplazado = "reemplazado"
    modificado = "modificado"
    en_revision = "en_revision"
    desconocido = "desconocido"


class ProcessingStatusEnum(str, enum.Enum):
    pendiente = "pendiente"
    procesando = "procesando"
    procesado = "procesado"
    error = "error"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.consulta)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_uuid)

    # Metadatos institucionales (sección 5 del prompt)
    nombre = Column(String, nullable=False)
    tipo_documento = Column(String, nullable=True)  # resolución, circular, decreto, etc.
    numero = Column(String, nullable=True)
    fecha_documento = Column(DateTime, nullable=True)
    anio = Column(Integer, nullable=True)
    entidad_emisora = Column(String, nullable=True)
    dependencia = Column(String, nullable=True)
    tema = Column(String, nullable=True)  # categoría (convivencia escolar, matrícula, etc.)
    version = Column(String, nullable=True)
    estado_vigencia = Column(Enum(VigenciaEnum), nullable=False, default=VigenciaEnum.desconocido)
    reemplazado_por_id = Column(String, ForeignKey("documents.id"), nullable=True)

    url_original = Column(String, nullable=True)
    ruta_archivo = Column(String, nullable=False)  # ubicación en disco/almacenamiento
    formato = Column(String, nullable=False)  # pdf/docx/txt

    requirio_ocr = Column(Boolean, default=False)
    estado_procesamiento = Column(Enum(ProcessingStatusEnum), default=ProcessingStatusEnum.pendiente)
    error_procesamiento = Column(Text, nullable=True)

    es_demo = Column(Boolean, default=False)  # marca datos ficticios de prueba

    fecha_carga = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    subido_por_id = Column(String, ForeignKey("users.id"), nullable=True)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=gen_uuid)
    chunk_id = Column(String, unique=True, index=True)  # p.ej. RES0015-P08-C03
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)

    texto = Column(Text, nullable=False)
    pagina = Column(Integer, nullable=True)
    articulo = Column(String, nullable=True)
    numeral = Column(String, nullable=True)
    apartado = Column(String, nullable=True)
    orden = Column(Integer, nullable=False)  # posición dentro del documento

    vector_ref = Column(String, nullable=True)  # id en el índice vectorial (faiss_local)
    # embedding = Column(Vector(dim))  # habilitar si VECTOR_BACKEND=pgvector

    document = relationship("Document", back_populates="chunks")


class QueryLog(Base):
    """Registro de auditoría de cada consulta (sección 10)."""
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    pregunta = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=True)
    respondido = Column(Boolean, default=False)  # False si fue "sin información suficiente"
    nivel_confianza = Column(String, nullable=True)  # alta / media / baja
    chunks_recuperados = Column(JSON, nullable=True)  # lista de chunk_ids usados
    modelo_utilizado = Column(String, nullable=True)
    tiempo_respuesta_ms = Column(Integer, nullable=True)
    valoracion = Column(Integer, nullable=True)  # 1-5, opcional, dado por el usuario
    creado_en = Column(DateTime, default=datetime.utcnow)
