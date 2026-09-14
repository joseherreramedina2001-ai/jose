-- Migración inicial para producción (PostgreSQL + pgvector).
-- En desarrollo, las tablas equivalentes se crean automáticamente vía
-- SQLAlchemy (backend/models/models.py) sobre SQLite. Este script es la
-- referencia para producción, donde además se activa la búsqueda vectorial
-- nativa en la propia base relacional (sección 3 del prompt).
--
-- Nota: si se usa esta migración, backend/rag/vector_store.py debe
-- implementarse con consultas SQL usando el operador `<=>` de pgvector
-- (distancia coseno) en lugar del backend faiss_local. La interfaz
-- VectorStore ya está preparada para ese reemplazo sin tocar el resto
-- del pipeline RAG.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    role VARCHAR NOT NULL DEFAULT 'consulta',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR NOT NULL,
    tipo_documento VARCHAR,
    numero VARCHAR,
    fecha_documento TIMESTAMP,
    anio INTEGER,
    entidad_emisora VARCHAR,
    dependencia VARCHAR,
    tema VARCHAR,
    version VARCHAR,
    estado_vigencia VARCHAR NOT NULL DEFAULT 'desconocido',
    reemplazado_por_id UUID REFERENCES documents(id),
    url_original VARCHAR,
    ruta_archivo VARCHAR NOT NULL,
    formato VARCHAR NOT NULL,
    requirio_ocr BOOLEAN DEFAULT FALSE,
    estado_procesamiento VARCHAR DEFAULT 'pendiente',
    error_procesamiento TEXT,
    es_demo BOOLEAN DEFAULT FALSE,
    fecha_carga TIMESTAMP DEFAULT now(),
    fecha_actualizacion TIMESTAMP DEFAULT now(),
    subido_por_id UUID REFERENCES users(id)
);

-- Dimensión de ejemplo (384) para el modelo multilingüe MiniLM por defecto.
-- Ajustar si se cambia EMBEDDING_MODEL (p.ej. 1536 para embeddings de OpenAI).
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id VARCHAR UNIQUE NOT NULL,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    texto TEXT NOT NULL,
    pagina INTEGER,
    articulo VARCHAR,
    numeral VARCHAR,
    apartado VARCHAR,
    orden INTEGER NOT NULL,
    embedding vector(384)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    pregunta TEXT NOT NULL,
    respuesta TEXT,
    respondido BOOLEAN DEFAULT FALSE,
    nivel_confianza VARCHAR,
    chunks_recuperados JSONB,
    modelo_utilizado VARCHAR,
    tiempo_respuesta_ms INTEGER,
    valoracion INTEGER,
    creado_en TIMESTAMP DEFAULT now()
);
