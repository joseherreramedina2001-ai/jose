from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.session import Base, engine
from backend.api.routes import auth, documents, chat, admin

# Crea las tablas si no existen. En SQLite (desarrollo) esto define el
# esquema completo. En PostgreSQL de producción, el esquema real (incluida
# la columna `embedding vector(...)` de pgvector) lo define
# database/001_init_pgvector.sql, ejecutado por Postgres al iniciar el
# contenedor (docker-entrypoint-initdb.d) antes de que el backend arranque;
# create_all() no modifica columnas de tablas ya existentes, así que no
# hay conflicto entre ambos caminos.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Asistente Virtual Inteligente de la Secretaría de Educación",
    description="Motor de consulta documental institucional basado en RAG.",
    version="0.1.0-mvp",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
