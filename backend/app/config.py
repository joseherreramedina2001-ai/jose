from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/sec_educacion"

    embedding_provider: str = "local"

    llm_provider: str = "extractive"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    upload_dir: str = "./uploads"
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 6
    similarity_threshold: float = 0.35

    cors_origins: str = "http://localhost:5173"

    # Sincronización con Google Drive (opcional). Requiere una cuenta de servicio de
    # Google Cloud con la API de Drive habilitada y con acceso de lectura a la carpeta.
    google_drive_folder_id: str = ""
    google_service_account_json: str = ""
    google_application_credentials: str = ""
    drive_sync_interval_minutes: int = 30  # 0 desactiva la sincronización automática


@lru_cache
def get_settings() -> Settings:
    return Settings()
