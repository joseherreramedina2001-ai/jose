# Asistente Virtual Inteligente de la Secretaría de Educación

Motor de consulta documental institucional basado en RAG (Retrieval-Augmented
Generation). Permite preguntar en lenguaje natural sobre normativa y documentación
oficial (resoluciones, circulares, decretos, protocolos, etc.) y obtener respuestas
fundamentadas exclusivamente en los documentos cargados, con sus fuentes citadas.

**Principio fundamental**: el sistema nunca inventa normativa. Si no hay fragmentos
recuperados con suficiente similitud, responde explícitamente que no tiene información
suficiente en lugar de generar una respuesta (ver `backend/app/services/llm_provider.py`).

## Estado de este esqueleto

Este es el andamiaje completo del sistema descrito en el spec: la arquitectura, los
modelos de datos, el pipeline RAG de punta a punta y las pantallas principales están
implementados y funcionan entre sí. Algunas partes quedan como puntos de extensión
señalados en el código (buscar `NotImplementedError` y comentarios "esqueleto"/"TODO").

**Implementado y funcional:**
- Carga de documentos (PDF/DOCX/TXT) → extracción de texto → chunking → embeddings →
  almacenamiento vectorial (pgvector).
- Consulta en lenguaje natural → búsqueda semántica → generación de respuesta con
  fuentes citadas (documento, número, año, página, estado de vigencia).
- Salvaguarda anti-alucinación: sin fragmentos relevantes, respuesta estándar de "no
  encontré información suficiente"; nunca se inventa contenido normativo.
- Control de vigencia (vigente/derogado/reemplazado/modificado/en revisión/desconocido)
  y aviso cuando la respuesta mezcla documentos con distinto estado o vigencia.
- Panel administrativo: carga y gestión de documentos, cambio de estado de vigencia,
  estadísticas (documentos, consultas, tiempo promedio, satisfacción).
- Auditoría: cada consulta registra usuario, pregunta, fragmentos recuperados,
  respuesta, modelo usado y tiempo de respuesta (`/api/admin/audit`).
- Proveedores de IA intercambiables por configuración, sin código acoplado a un solo
  proveedor (ver "Proveedores de IA" abajo).

**Pendiente / puntos de extensión explícitos:**
- **OCR** para PDFs escaneados (`app/services/ingestion.py::run_ocr` — hoy se detecta y
  se marca el documento como error, pero no se procesa).
- **Autenticación real** (login, roles rector/coordinador/docente/admin). El modelo
  `User` y el campo `user_id` en auditoría ya existen; falta la capa de login/JWT.
  Todos los endpoints están abiertos por ahora.
- **Migraciones con Alembic** (hoy las tablas se crean automáticamente al iniciar; hay
  que introducir migraciones versionadas antes de producción).
- **Cola de tareas en segundo plano** para indexar documentos grandes sin bloquear la
  respuesta HTTP (hoy la indexación es síncrona).
- **Detección de conflictos más fina** entre disposiciones (hoy se avisa cuando hay
  fragmentos de documentos con distinto estado de vigencia; un análisis semántico más
  profundo de contradicciones queda para una siguiente iteración).
- **Article/numeral/section por chunk**: los campos existen en el modelo pero la
  extracción automática de "artículo X" / "numeral Y" desde el texto aún no está
  implementada (hoy solo se detecta la página).

## Arquitectura

```
Usuario → Pregunta → Normalización → Embedding → Búsqueda semántica (pgvector)
        → Fragmentos relevantes → Detección de vigencia/conflictos → LLM → Respuesta + Fuentes
```

- **Frontend**: React + TypeScript + Vite + Tailwind CSS (`frontend/`).
- **Backend**: Python + FastAPI, arquitectura modular por routers/servicios/modelos
  (`backend/`).
- **Base de datos**: PostgreSQL + pgvector (usuarios, documentos, fragmentos con
  embeddings, categorías, interacciones/auditoría).

## Proveedores de IA (pensado para poder empezar gratis)

Configurables por variables de entorno, sin tocar código:

- **Embeddings** (`EMBEDDING_PROVIDER`): `local` (por defecto) usa
  `sentence-transformers` corriendo en tu propia máquina — gratis, sin API key.
- **LLM** (`LLM_PROVIDER`): `extractive` (por defecto) no llama a ningún proveedor
  externo — ensambla la respuesta directamente desde los fragmentos recuperados, costo
  cero. `anthropic` activa respuestas generativas vía la API de Anthropic (requiere
  `ANTHROPIC_API_KEY`).

Cuando tengas tus documentos cargados, la app ya es utilizable en modo 100% gratuito;
activar un LLM generativo es un cambio de una variable de entorno.

## Puesta en marcha

### 1. Base de datos

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.seed_categories   # carga las categorías temáticas por defecto
uvicorn app.main:app --reload
```

API disponible en `http://localhost:8000` (docs interactivas en `/docs`).

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App disponible en `http://localhost:5173` (proxy configurado hacia el backend).

### 4. Cargar documentos

Desde el panel administrativo (`/admin`) o vía `POST /api/documents` (multipart:
`file`, `title`, `doc_type`, y metadatos opcionales). El documento se indexa
automáticamente al subirlo.

## Estructura del repositorio

```
backend/
  app/
    models/       # User, Document, DocumentChunk, Category, Interaction (SQLAlchemy)
    routers/       # documents, query, admin, categories (FastAPI)
    services/
      ingestion.py     # extracción de texto (PDF/DOCX/TXT) y chunking
      embeddings.py     # proveedor de embeddings (intercambiable)
      llm_provider.py   # proveedor de LLM + prompt de sistema (intercambiable)
      indexing.py        # orquesta la indexación de un documento
      rag_pipeline.py    # orquesta una consulta de punta a punta
      vector_store.py    # búsqueda por similitud en pgvector
    schemas.py    # contratos Pydantic de la API
    config.py     # configuración vía variables de entorno
  scripts/seed_categories.py
frontend/
  src/
    pages/Home.tsx     # pantalla de consulta
    pages/Admin.tsx    # panel administrativo
    components/         # QueryBox, AnswerCard, SourceList, History
    api/client.ts        # cliente HTTP hacia el backend
docker-compose.yml   # PostgreSQL + pgvector
```
