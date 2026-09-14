# Asistente Virtual Inteligente de la Secretaría de Educación

Motor de consulta documental institucional basado en RAG (Retrieval-Augmented
Generation). Permite a rectores, coordinadores, docentes y funcionarios
consultar normativa y documentación oficial en lenguaje natural, con
respuestas trazables a sus fuentes y sin inventar información.

> **Estado del proyecto:** MVP funcional. El pipeline completo (carga →
> extracción → OCR si aplica → chunking → embeddings → indexación →
> recuperación → generación fundamentada → fuentes) está implementado y
> probado. Ver "Limitaciones conocidas" antes de llevarlo a producción.

## Principio fundamental

**La IA no debe inventar, completar, asumir ni especular información
normativa.** Si no hay fragmentos institucionales suficientemente
relacionados con la pregunta, el sistema responde:

> "No encontré información suficiente en la documentación institucional
> disponible para responder esta consulta con seguridad..."

Este guardrail vive en un único punto del código
(`backend/rag/generator.py::responder_pregunta`) y está cubierto por
pruebas automáticas en `tests/test_generator_guardrail.py`.

## Arquitectura

```
Usuario → Pregunta → Embedding de la consulta → Búsqueda vectorial
        → Priorización por vigencia → ¿Similitud suficiente?
             │ no                          │ sí
             ▼                             ▼
   "Información insuficiente"    LLM (solo con los fragmentos) → Respuesta + Fuentes
```

- **Frontend:** React + TypeScript + Vite + Tailwind CSS.
- **Backend:** FastAPI (Python), arquitectura modular por capas.
- **Base de datos:** PostgreSQL + pgvector en producción; SQLite + FAISS
  local en desarrollo (mismo código, backend intercambiable por variable
  de entorno).
- **IA:** capa de proveedor desacoplada — OpenAI, Anthropic o un
  `MockProvider` de demostración, sin acoplar el sistema a uno solo.

### Estructura del proyecto

```
/frontend                  React + TS + Tailwind
/backend
  /api/routes               Endpoints (auth, documents, chat, admin)
  /core                      Configuración (variables de entorno)
  /models                    Modelos SQLAlchemy
  /services                  Orquestación del pipeline de ingestión
  /rag                       Chunking, retrieval, generación, guardrail
  /documents                 Extracción de texto y OCR
  /embeddings                Proveedores de embeddings
  /database                  Sesión de base de datos
  /auth                      JWT, hashing, control de roles
  /utils                     Scripts de utilidad (crear admin, etc.)
/database                   Migración SQL con pgvector (producción)
/tests                      Pruebas automatizadas (pytest)
/.env.example
/docker-compose.yml
```

## Tecnologías y por qué

| Capa | Elección | Motivo |
|---|---|---|
| Embeddings por defecto | `sentence-transformers` (local) | No requiere enviar documentos normativos a un proveedor externo ni claves API para operar. |
| Vector store dev | FAISS local | Cero infraestructura adicional para probar el sistema. |
| Vector store prod | PostgreSQL + pgvector | Una sola base de datos para todo (sin operar un vector DB aparte). |
| LLM | Abstracto (OpenAI/Anthropic/mock) | Evita acoplar la arquitectura RAG a un proveedor específico (sección 23 del diseño). |

## Instalación

### Requisitos

- Python 3.11+
- Node.js 20+
- Docker y Docker Compose (para el stack de producción con Postgres)
- Para OCR: `tesseract-ocr` y `poppler-utils` instalados en el sistema
  (ya incluidos en `backend/Dockerfile`)

### Desarrollo local (sin Docker, con SQLite + FAISS)

```bash
# Backend
cp .env.example .env
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m backend.utils.create_admin admin@ejemplo.gov.co "ClaveSegura123!" "Nombre Apellido"
uvicorn backend.main:app --reload

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

La app queda disponible en `http://localhost:5173` (frontend) y
`http://localhost:8000/docs` (documentación interactiva de la API).

### Producción (Docker Compose, con PostgreSQL + pgvector)

```bash
cp .env.example .env
# Editar .env: SECRET_KEY, LLM_PROVIDER, LLM_API_KEY, etc.
docker compose up --build -d

# Crear el primer administrador dentro del contenedor backend
docker compose exec backend python -m backend.utils.create_admin \
  admin@secretariaeducacion.gov.co "ClaveSegura123!" "Nombre Apellido"
```

`docker-compose.yml` levanta:
- `db`: PostgreSQL con la extensión pgvector, inicializado con
  `database/001_init_pgvector.sql`.
- `backend`: la API FastAPI, con `VECTOR_BACKEND=pgvector`.
- `frontend`: el build de producción servido por nginx, con proxy a `/api`.

## Variables de entorno

Ver `.env.example`. Las más relevantes:

- `DATABASE_URL`: cadena de conexión. SQLite en desarrollo, Postgres en producción.
- `VECTOR_BACKEND`: `faiss_local` o `pgvector`.
- `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_MODEL`: proveedor de generación.
- `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL`: proveedor de embeddings.
- `MIN_SIMILARITY_THRESHOLD`: umbral por debajo del cual el sistema se
  niega a responder normativamente (guardrail anti-alucinación).
- `OCR_ENABLED`: activa el flujo de OCR para PDFs escaneados.

**Nunca** se incluyen claves reales en el repositorio; `.env` está en
`.gitignore`.

## Procesamiento documental

Al cargar un documento (`POST /api/documents/upload`):

1. Se valida extensión (`.pdf`, `.docx`, `.txt`) y tamaño máximo.
2. Se extrae el texto. En PDF, si el promedio de caracteres por página es
   muy bajo, se asume que es un escaneo y se envía a OCR
   (`pytesseract` + `pdf2image`, idioma español).
3. Se divide en fragmentos (`chunk_size` configurable, con solapamiento)
   conservando página de origen y, cuando se detectan, artículo/numeral.
4. Se generan embeddings y se indexan.
5. Se guarda el vínculo fragmento ↔ documento (`chunk_id` trazable, p. ej.
   `RES-2026-0015-P08-C03`).

El estado de procesamiento (`pendiente` / `procesando` / `procesado` /
`error`) es visible desde el panel administrativo.

## El guardrail anti-alucinación, en detalle

`backend/rag/generator.py::responder_pregunta` es el único punto de
entrada para generar una respuesta, y aplica, en orden:

1. Si no hay ningún fragmento recuperado → mensaje de información
   insuficiente, sin llamar al LLM.
2. Si el mejor fragmento está por debajo de `MIN_SIMILARITY_THRESHOLD` →
   mensaje de "no se encontraron fuentes suficientemente relacionadas",
   sin llamar al LLM.
3. Si hay fragmentos suficientes pero de documentos con distinto estado de
   vigencia sobre un tema similar → se advierte al LLM explícitamente para
   que señale la posible contradicción en vez de elegir arbitrariamente.
4. Solo entonces se llama al LLM, y únicamente con los fragmentos
   recuperados como contexto (el `system_prompt` en
   `backend/rag/system_prompt.py` se lo prohíbe explícitamente usar
   conocimiento externo).

Toda consulta queda auditada en `query_logs`, incluyendo si fue
respondida o no y qué `chunk_id`s se usaron.

## Ejecución de pruebas

```bash
cd backend  # o desde la raíz, ajustando PYTHONPATH
pip install -r requirements.txt
pytest ../tests -v
```

Cobertura actual:
- **Chunking:** trazabilidad de `chunk_id`, solapamiento, páginas vacías.
- **Extracción:** validación de archivos, formatos vacíos.
- **Guardrail anti-alucinación:** sin fragmentos, baja similitud,
  respuesta con fuentes, detección de contradicción — el núcleo del
  sistema (sección 25 del diseño original).
- **Seguridad:** acceso sin token, token inválido, control de roles por
  endpoint, rechazo de extensiones de archivo no permitidas.

## Datos de prueba (DEMO)

Los documentos institucionales reales **no** se incluyen ni se inventan.
El campo `es_demo` en `Document` permite marcar explícitamente cualquier
documento de prueba cargado durante el desarrollo, para no confundirlo
jamás con normativa real. La interfaz de administración muestra una
etiqueta "DEMO" junto a estos documentos.

## Limitaciones conocidas (a resolver antes de producción)

- **Borrado en FAISS local:** el backend `faiss_local` no soporta borrado
  eficiente de vectores por documento; en producción, usar
  `VECTOR_BACKEND=pgvector`, donde el borrado en cascada sí es nativo.
- **Migraciones:** el esquema de producción se aplica con un único script
  SQL (`database/001_init_pgvector.sql`). Para evolucionar el esquema con
  el tiempo, se recomienda introducir Alembic.
- **Detección de contradicciones:** la heurística actual
  (`backend/rag/retriever.py::_detectar_contradiccion`) compara tema y
  estado de vigencia entre los documentos mejor rankeados; un sistema más
  maduro añadiría un paso de verificación de entailment/contradicción con
  el propio LLM antes de responder.
- **Dimensión del embedding en pgvector:** la migración fija
  `vector(384)` (modelo multilingüe MiniLM por defecto). Si se cambia
  `EMBEDDING_MODEL` a uno con otra dimensión, hay que ajustar la columna.
- **Autenticación:** el MVP no incluye recuperación de contraseña ni
  expiración/rotación de tokens de refresco; el token de acceso expira
  según `ACCESS_TOKEN_EXPIRE_MINUTES` y requiere volver a iniciar sesión.
- **Rate limiting:** no implementado aún sobre los endpoints públicos de
  autenticación; recomendable antes de exponerlo a internet.

## Próximos pasos sugeridos

1. Cargar un conjunto piloto de documentos reales (marcados como no-DEMO)
   y calibrar `MIN_SIMILARITY_THRESHOLD` con casos reales del sector.
2. Añadir búsqueda híbrida (semántica + palabras clave) para mejorar
   recall en textos con numeración legal exacta (artículos, numerales).
3. Integrar Alembic para migraciones versionadas.
4. Añadir panel de auditoría en el frontend (actualmente solo expuesto
   por API en `GET /api/admin/audit`).
