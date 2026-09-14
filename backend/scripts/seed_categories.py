"""Carga las categorías temáticas por defecto (sección 11 del spec).
Uso: python -m scripts.seed_categories (desde backend/, con el entorno virtual activo)
"""

from app.database import Base, SessionLocal, engine
from app.models import Category

DEFAULT_CATEGORIES = [
    "Convivencia escolar",
    "Gestión académica",
    "Talento humano",
    "Matrícula",
    "Evaluación",
    "Inclusión",
    "Infraestructura",
    "Contratación",
    "Calidad educativa",
    "Planeación",
    "Administración",
    "Seguridad",
    "Otros",
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = {c.name for c in db.query(Category).all()}
        for name in DEFAULT_CATEGORIES:
            if name not in existing:
                db.add(Category(name=name))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
