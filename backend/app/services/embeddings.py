"""Proveedores de embeddings, intercambiables vía configuración (EMBEDDING_PROVIDER)."""

from abc import ABC, abstractmethod

from app.config import get_settings


class EmbeddingProvider(ABC):
    dimension: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LocalEmbeddingProvider(EmbeddingProvider):
    """Embeddings locales y gratuitos vía sentence-transformers. No requiere API key ni
    tiene costo por uso; corre en la propia infraestructura."""

    dimension = 384

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()


_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is None:
        settings = get_settings()
        if settings.embedding_provider == "local":
            _provider = LocalEmbeddingProvider()
        else:
            raise ValueError(f"Proveedor de embeddings no soportado: {settings.embedding_provider}")
    return _provider
