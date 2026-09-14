import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 - registra los modelos antes de create_all
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routers import admin, categories, documents, drive, query
from app.services.drive_sync import sync_drive_folder

logger = logging.getLogger("uvicorn.error")
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


async def _drive_sync_loop():
    interval_seconds = settings.drive_sync_interval_minutes * 60
    while True:
        await asyncio.sleep(interval_seconds)
        db = SessionLocal()
        try:
            result = sync_drive_folder(db)
            logger.info("Sincronización de Google Drive completada: %s", result)
        except Exception:
            logger.exception("Falló la sincronización automática con Google Drive")
        finally:
            db.close()


@app.on_event("startup")
def on_startup():
    # Etapa de esqueleto: crea las tablas automáticamente. Sustituir por migraciones
    # de Alembic antes de un despliegue en producción.
    Base.metadata.create_all(bind=engine)

    if settings.google_drive_folder_id and settings.drive_sync_interval_minutes > 0:
        asyncio.create_task(_drive_sync_loop())


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(documents.router)
app.include_router(query.router)
app.include_router(admin.router)
app.include_router(categories.router)
app.include_router(drive.router)
