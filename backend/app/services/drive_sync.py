"""Sincronización de documentos desde una carpeta de Google Drive.

Requiere una cuenta de servicio de Google Cloud con la API de Drive habilitada, y que
la carpeta de origen esté compartida (al menos como "Lector") con el correo de esa
cuenta de servicio. Ver README para el paso a paso de configuración.

Los archivos nativos de Google (Documentos de Google) se exportan a PDF antes de
descargarlos, porque no tienen una representación binaria propia.
"""

import io
import json
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Document, DocumentSource, DocumentStatus
from app.services.indexing import index_document

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# mimeType nativo de Google -> (mimeType de exportación, extensión de destino)
EXPORTABLE_GOOGLE_TYPES = {
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
}

# mimeType descargable directamente -> extensión de destino
DOWNLOADABLE_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}


def _build_drive_client():
    settings = get_settings()
    if settings.google_service_account_json:
        info = json.loads(settings.google_service_account_json)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    elif settings.google_application_credentials:
        credentials = service_account.Credentials.from_service_account_file(
            settings.google_application_credentials, scopes=SCOPES
        )
    else:
        raise ValueError(
            "Configura GOOGLE_SERVICE_ACCOUNT_JSON o GOOGLE_APPLICATION_CREDENTIALS "
            "para sincronizar con Google Drive."
        )
    return build("drive", "v3", credentials=credentials)


def _list_folder_files(drive, folder_id: str) -> list[dict]:
    files = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"
    while True:
        response = (
            drive.files()
            .list(q=query, fields="nextPageToken, files(id, name, mimeType, modifiedTime)", pageToken=page_token)
            .execute()
        )
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return files


def _target_extension(mime_type: str) -> str | None:
    if mime_type in EXPORTABLE_GOOGLE_TYPES:
        return EXPORTABLE_GOOGLE_TYPES[mime_type][1]
    return DOWNLOADABLE_TYPES.get(mime_type)


def _download_file(drive, file_id: str, mime_type: str, dest: Path) -> None:
    if mime_type in EXPORTABLE_GOOGLE_TYPES:
        export_mime, _ = EXPORTABLE_GOOGLE_TYPES[mime_type]
        request = drive.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        request = drive.files().get_media(fileId=file_id)

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    dest.write_bytes(buffer.getvalue())


def sync_drive_folder(db: Session) -> dict:
    """Revisa la carpeta configurada de Google Drive, descarga los documentos nuevos o
    modificados desde la última sincronización, y los indexa automáticamente. Los
    documentos ya sincronizados que no cambiaron se omiten (comparando modifiedTime)."""
    settings = get_settings()
    if not settings.google_drive_folder_id:
        raise ValueError("Configura GOOGLE_DRIVE_FOLDER_ID para sincronizar con Google Drive.")

    drive = _build_drive_client()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    remote_files = _list_folder_files(drive, settings.google_drive_folder_id)

    created = updated = skipped = unchanged = 0

    for remote in remote_files:
        mime_type = remote["mimeType"]
        ext = _target_extension(mime_type)
        if not ext:
            skipped += 1
            continue

        modified_at = datetime.fromisoformat(remote["modifiedTime"].replace("Z", "+00:00")).replace(tzinfo=None)

        existing = (
            db.query(Document)
            .filter(Document.source == DocumentSource.GOOGLE_DRIVE, Document.external_id == remote["id"])
            .first()
        )
        if existing and existing.external_modified_at and existing.external_modified_at >= modified_at:
            unchanged += 1
            continue

        document = existing or Document(
            source=DocumentSource.GOOGLE_DRIVE,
            external_id=remote["id"],
            doc_type="otro",
            status=DocumentStatus.DESCONOCIDO,
            file_path="",
        )
        document.title = remote["name"]
        document.external_modified_at = modified_at
        db.add(document)
        db.flush()

        dest = upload_dir / f"{document.id}{ext}"
        try:
            _download_file(drive, remote["id"], mime_type, dest)
        except Exception:
            skipped += 1
            continue

        document.file_path = str(dest)
        for chunk in list(document.chunks):
            db.delete(chunk)
        db.commit()

        try:
            index_document(db, document)
        except Exception:
            pass  # el estado de error queda registrado en document.indexing_status

        if existing:
            updated += 1
        else:
            created += 1

    return {
        "total_seen": len(remote_files),
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "skipped": skipped,
    }
