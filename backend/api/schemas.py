from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str

    class Config:
        from_attributes = True


# --- Documents ---
class DocumentMetadataIn(BaseModel):
    nombre: str
    tipo_documento: Optional[str] = None
    numero: Optional[str] = None
    fecha_documento: Optional[datetime] = None
    anio: Optional[int] = None
    entidad_emisora: Optional[str] = None
    dependencia: Optional[str] = None
    tema: Optional[str] = None
    version: Optional[str] = None
    estado_vigencia: Optional[str] = "desconocido"
    url_original: Optional[str] = None
    es_demo: bool = False


class DocumentOut(BaseModel):
    id: str
    nombre: str
    tipo_documento: Optional[str]
    numero: Optional[str]
    anio: Optional[int]
    tema: Optional[str]
    estado_vigencia: str
    estado_procesamiento: str
    requirio_ocr: bool
    formato: str
    es_demo: bool
    fecha_carga: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class DocumentUpdateMetadata(BaseModel):
    tema: Optional[str] = None
    estado_vigencia: Optional[str] = None
    version: Optional[str] = None
    reemplazado_por_id: Optional[str] = None


# --- Chat ---
class ChatQueryRequest(BaseModel):
    pregunta: str


class FuenteOut(BaseModel):
    documento_nombre: str
    tipo_documento: Optional[str]
    numero: Optional[str]
    anio: Optional[int]
    estado_vigencia: str
    pagina: Optional[int]
    apartado: Optional[str]
    articulo: Optional[str]
    chunk_id: str
    url_original: Optional[str]


class ChatQueryResponse(BaseModel):
    respondido: bool
    respuesta: str
    fuentes: List[FuenteOut]
    nivel_confianza: str
    posible_contradiccion: bool
    query_log_id: str


class RatingRequest(BaseModel):
    valoracion: int  # 1-5


# --- Admin ---
class StatisticsOut(BaseModel):
    total_documentos: int
    documentos_procesados: int
    documentos_pendientes: int
    documentos_error: int
    total_consultas: int
    consultas_sin_respuesta: int
    tiempo_promedio_respuesta_ms: Optional[float]
