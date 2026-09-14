import os
import sys
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["LLM_PROVIDER"] = "mock"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy.orm import Session

from backend.database.session import Base, engine, SessionLocal
from backend.models.models import User, RoleEnum
from backend.auth.security import hash_password


@pytest.fixture()
def db() -> Session:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def admin_user(db):
    user = User(email="admin@test.gov.co", hashed_password=hash_password("Clave123!"), role=RoleEnum.admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def consulta_user(db):
    user = User(email="consulta@test.gov.co", hashed_password=hash_password("Clave123!"), role=RoleEnum.consulta)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def client(db):
    """TestClient que reutiliza la sesión de BD de la prueba (override de get_db)."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.database.session import get_db

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def token_for(user):
    from backend.auth.security import create_access_token
    return create_access_token(subject=user.id, role=user.role.value)
