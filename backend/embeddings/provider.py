"""
Abstracción de embeddings (sección 23): el resto del sistema solo conoce
`embed_texts(list[str]) -> list[list[float]]`, sin importar el proveedor.
"""
from abc import ABC, abstractmethod
from typing import List
from functools import lru_cache

from backend.core.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        ...

    @abstractmethod
    def dimension(self) -> int:
        ...


class SentenceTransformersProvider(EmbeddingProvider):
    """Embeddings locales, sin dependencia de una API externa ni de claves.
    Recomendado por defecto para instituciones que no quieren enviar
    documentos normativos a un proveedor externo."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str, api_key: str):
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key)
        self._model_name = model_name

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        resp = self._client.embeddings.create(model=self._model_name, input=texts)
        return [d.embedding for d in resp.data]

    def dimension(self) -> int:
        return 1536  # depende del modelo elegido; ajustar si se cambia


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    if settings.EMBEDDING_PROVIDER == "sentence_transformers":
        return SentenceTransformersProvider(settings.EMBEDDING_MODEL)
    elif settings.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingProvider(settings.EMBEDDING_MODEL, settings.LLM_API_KEY)
    else:
        raise NotImplementedError(f"Proveedor de embeddings no implementado: {settings.EMBEDDING_PROVIDER}")
