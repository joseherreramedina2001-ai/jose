from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 - registra los modelos antes de create_all
from app.config import get_settings
from app.database import Base, engine
from app.routers import admin, categories, documents, query

settings = get_settings()

app = FastAPI(
    title="Asistente Virtual Inteligente - Secretaría de Educación",
    description="Motor de consulta documental institucional basado en RAG.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Etapa de esqueleto: crea las tablas automáticamente. Sustituir por migraciones
    # de Alembic antes de un despliegue en producción.
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(documents.router)
app.include_router(query.router)
app.include_router(admin.router)
app.include_router(categories.router)
