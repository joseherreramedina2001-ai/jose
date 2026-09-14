"""
Almacén vectorial desacoplado del motor de recuperación.

- faiss_local: para desarrollo/pruebas sin infraestructura adicional.
- pgvector: para producción (usa la misma base de datos relacional,
  simplifica la operación institucional). Ver database/migrations/ para
  el DDL con la columna `embedding vector(dim)`.

Ambos exponen la misma interfaz: add(), search(), delete_by_document().
"""
import os
import pickle
from abc import ABC, abstractmethod
from typing import List, Tuple

import numpy as np

from backend.core.config import settings


class VectorStore(ABC):
    @abstractmethod
    def add(self, ids: List[str], vectors: List[List[float]], document_id: str):
        ...

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int) -> List[Tuple[str, float]]:
        """Devuelve lista de (vector_ref_id, score_similitud) ordenada desc."""
        ...

    @abstractmethod
    def delete_by_document(self, document_id: str):
        ...


class FaissLocalStore(VectorStore):
    """Índice FAISS simple persistido en disco (plano, coseno vía normalización).
    Adecuado para MVP/demo; para volúmenes grandes en producción se recomienda
    migrar a pgvector con índice IVFFlat/HNSW."""

    def __init__(self, path: str, dim: int | None = None):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._dim = dim
        self._ids: List[str] = []
        self._doc_of_id: dict[str, str] = {}
        self._index = None
        self._load()

    def _load(self):
        import faiss
        if os.path.exists(self.path) and os.path.exists(self.path + ".meta"):
            self._index = faiss.read_index(self.path)
            with open(self.path + ".meta", "rb") as f:
                meta = pickle.load(f)
                self._ids = meta["ids"]
                self._doc_of_id = meta["doc_of_id"]
                self._dim = meta["dim"]
        elif self._dim:
            self._index = faiss.IndexFlatIP(self._dim)  # producto interno = coseno si está normalizado

    def _save(self):
        import faiss
        faiss.write_index(self._index, self.path)
        with open(self.path + ".meta", "wb") as f:
            pickle.dump({"ids": self._ids, "doc_of_id": self._doc_of_id, "dim": self._dim}, f)

    def add(self, ids: List[str], vectors: List[List[float]], document_id: str):
        import faiss
        arr = np.array(vectors, dtype="float32")
        if self._index is None:
            self._dim = arr.shape[1]
            self._index = faiss.IndexFlatIP(self._dim)
        self._index.add(arr)
        self._ids.extend(ids)
        for i in ids:
            self._doc_of_id[i] = document_id
        self._save()

    def search(self, query_vector: List[float], top_k: int) -> List[Tuple[str, float]]:
        if self._index is None or self._index.ntotal == 0:
            return []
        q = np.array([query_vector], dtype="float32")
        scores, idxs = self._index.search(q, min(top_k, self._index.ntotal))
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append((self._ids[idx], float(score)))
        return results

    def delete_by_document(self, document_id: str):
        # FAISS plano no soporta borrado eficiente por id; para un MVP se
        # reconstruye el índice sin los vectores del documento eliminado.
        # En producción, usar pgvector (DELETE nativo) evita esta limitación.
        raise NotImplementedError(
            "Borrado no soportado en el backend faiss_local del MVP. "
            "Usar VECTOR_BACKEND=pgvector en producción para esta operación."
        )


class PgVectorStore(VectorStore):
    """Backend de producción: usa la misma base relacional (PostgreSQL +
    extensión pgvector), evitando infraestructura adicional. Opera
    directamente sobre la tabla `document_chunks.embedding` mediante SQL,
    para no acoplar el vector store a los modelos ORM (que deben soportar
    también el modo faiss_local sin la columna `embedding` poblada).

    Contrato de uso: los chunks (chunk_id) deben existir ya en
    `document_chunks` antes de llamar a `add()`, porque aquí solo se
    actualiza la columna `embedding` de filas existentes. Ver
    services/document_processor.py para el orden correcto del pipeline.
    """

    def __init__(self, database_url: str):
        import psycopg
        from pgvector.psycopg import register_vector

        # SQLAlchemy usa el prefijo postgresql+psycopg://; psycopg necesita postgresql://
        dsn = database_url.replace("postgresql+psycopg://", "postgresql://")
        self._conn = psycopg.connect(dsn, autocommit=True)
        register_vector(self._conn)

    def add(self, ids: List[str], vectors: List[List[float]], document_id: str):
        with self._conn.cursor() as cur:
            for chunk_id, vector in zip(ids, vectors):
                cur.execute(
                    "UPDATE document_chunks SET embedding = %s WHERE chunk_id = %s",
                    (vector, chunk_id),
                )

    def search(self, query_vector: List[float], top_k: int) -> List[Tuple[str, float]]:
        with self._conn.cursor() as cur:
            # <=> es distancia coseno en pgvector; se convierte a "similitud"
            # (1 - distancia) para mantener la misma semántica que FaissLocalStore
            # (score más alto = más relevante), usada por el retriever y sus umbrales.
            cur.execute(
                """
                SELECT chunk_id, 1 - (embedding <=> %s) AS similitud
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (query_vector, query_vector, top_k),
            )
            return [(row[0], float(row[1])) for row in cur.fetchall()]

    def delete_by_document(self, document_id: str):
        # No hace falta borrar el vector explícitamente: el DELETE de la fila
        # Document en cascada elimina sus DocumentChunk (y por tanto su
        # embedding) automáticamente. Se deja el método por conformidad con
        # la interfaz VectorStore.
        pass


def get_vector_store(dim: int | None = None) -> VectorStore:
    if settings.VECTOR_BACKEND == "faiss_local":
        return FaissLocalStore(settings.VECTOR_INDEX_PATH, dim=dim)
    elif settings.VECTOR_BACKEND == "pgvector":
        return PgVectorStore(settings.DATABASE_URL)
    raise ValueError(f"VECTOR_BACKEND desconocido: {settings.VECTOR_BACKEND}")
