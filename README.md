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

### Vincular con Claude (API de Anthropic)

Importante: **no es tu cuenta de claude.ai** (esa es una suscripción de consumidor sin
acceso por API). Es una API key aparte, con facturación por uso:

1. Entrá a [console.anthropic.com](https://console.anthropic.com), creá una cuenta/organización y generá una API key.
2. En tu `.env` (raíz del proyecto, para Docker) poné:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. En `backend/.env` (o las variables de entorno del servicio `backend` en
   `docker-compose.yml`) poné `LLM_PROVIDER=anthropic`.
4. Reiniciá el backend (`docker compose up -d --build backend`). A partir de ahí, cada
   consulta genera la respuesta con Claude en vez del modo extractivo.

## Carga automática de documentos desde Google Drive (opcional)

En vez de subir cada documento manualmente desde el panel administrativo, podés
sincronizar una carpeta de Google Drive: el backend la revisa (manualmente con el botón
"Sincronizar ahora", o automáticamente cada `DRIVE_SYNC_INTERVAL_MINUTES`) y descarga e
indexa los archivos nuevos o modificados.

**Configuración (una sola vez):**

1. En [Google Cloud Console](https://console.cloud.google.com/), creá un proyecto (o
   usá uno existente) y habilitá la **Google Drive API**.
2. Creá una **cuenta de servicio** (IAM y administración → Cuentas de servicio) y
   generale una clave en formato JSON — se descarga un archivo.
3. Abrí ese JSON, copiá el `client_email` (algo como
   `nombre@proyecto.iam.gserviceaccount.com`), y **compartí la carpeta de Drive** con
   ese correo (permiso de Lector alcanza).
4. Tomá el ID de la carpeta desde la URL de Drive:
   `https://drive.google.com/drive/folders/`**`ESTE_ES_EL_ID`**.
5. En tu `.env` (raíz del proyecto) poné:
   ```
   GOOGLE_DRIVE_FOLDER_ID=el-id-de-la-carpeta
   GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account", ... todo el contenido del JSON en una sola línea ...}
   DRIVE_SYNC_INTERVAL_MINUTES=30
   ```
6. `docker compose up -d --build`. Con `GOOGLE_DRIVE_FOLDER_ID` configurado, la
   sincronización automática arranca sola cada `DRIVE_SYNC_INTERVAL_MINUTES`; también
   podés dispararla en cualquier momento con el botón "Sincronizar ahora" en `/admin`.

**Formatos soportados desde Drive:** PDF, DOCX, TXT, y Documentos de Google (se
exportan a PDF automáticamente). Hojas de cálculo, presentaciones y otros formatos se
omiten por ahora (quedan contados como "omitidos" en el resultado de la sincronización).

## Puesta en marcha (opción recomendada: todo en Docker)

No hace falta instalar Python, Node ni ninguna dependencia manualmente — solo
[Docker Desktop](https://www.docker.com/products/docker-desktop/). Todo lo demás
(base de datos, backend, frontend) queda empaquetado y se levanta con un comando:

```bash
docker compose up -d --build
```

- App: `http://localhost:5173`
- API: `http://localhost:8000` (docs interactivas en `/docs`)

La primera vez tarda más porque descarga las imágenes base y el modelo de embeddings
(~80 MB); las siguientes veces arranca rápido (queda todo cacheado en volúmenes). Para
apagarlo: `docker compose down` (los datos y documentos cargados se conservan; para
borrarlos también, `docker compose down -v`).

Para activar respuestas generativas con Claude en vez del modo extractivo gratuito,
creá un archivo `.env` en la raíz del proyecto con `ANTHROPIC_API_KEY=tu-clave` antes
de levantar el stack.

### Alternativa: correrlo sin Docker (requiere Python y Node instalados)

<details>
<summary>Ver pasos manuales</summary>

**1. Base de datos**
```bash
docker compose up -d db
```

**2. Backend**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.seed_categories
uvicorn app.main:app --reload
```

**3. Frontend**
```bash
cd frontend
npm install
npm run dev
```

</details>

### Cargar documentos

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
