from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.drive_sync import sync_drive_folder

router = APIRouter(prefix="/api/admin/drive", tags=["drive"])


@router.post("/sync")
def sync_now(db: Session = Depends(get_db)):
    try:
        return sync_drive_folder(db)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
