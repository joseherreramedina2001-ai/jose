"""
Configuración central de la aplicación.
Lee todo desde variables de entorno. Nunca hardcodear claves aquí.
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "production", "test"] = "development"

    # Base de datos relacional + vectorial.
    # En producción: postgresql+psycopg://user:pass@host:5432/db (con pgvector)
    # En desarrollo/pruebas sin infraestructura: sqlite (fallback), ver database/session.py
    DATABASE_URL: str = "sqlite:///./dev.db"
    VECTOR_BACKEND: Literal["pgvector", "faiss_local"] = "faiss_local"
    VECTOR_INDEX_PATH: str = "./data/faiss_index"

    # Autenticación
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Proveedor de IA (abstracto, ver rag/llm_provider.py)
    LLM_PROVIDER: Literal["openai", "anthropic", "local", "mock"] = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-6"
    EMBEDDING_PROVIDER: Literal["sentence_transformers", "openai", "anthropic_voyage"] = "sentence_transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # OCR
    OCR_ENABLED: bool = True

    # RAG
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 80
    RETRIEVAL_TOP_K: int = 6
    MIN_SIMILARITY_THRESHOLD: float = 0.35  # por debajo de esto -> "sin información suficiente"

    # Archivos
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: tuple = (".pdf", ".docx", ".txt")
    UPLOAD_DIR: str = "./data/uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
