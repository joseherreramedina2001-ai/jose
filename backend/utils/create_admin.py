"""
Uso: python -m backend.utils.create_admin admin@ejemplo.gov.co ClaveSegura123 "Nombre Apellido"
"""
import sys

from backend.database.session import SessionLocal, Base, engine
from backend.models.models import User, RoleEnum
from backend.auth.security import hash_password


def main():
    if len(sys.argv) < 3:
        print("Uso: python -m backend.utils.create_admin <email> <password> [nombre]")
        sys.exit(1)

    email, password = sys.argv[1], sys.argv[2]
    nombre = sys.argv[3] if len(sys.argv) > 3 else None

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            print(f"Ya existe un usuario con el correo {email}")
            return
        user = User(email=email, hashed_password=hash_password(password), full_name=nombre, role=RoleEnum.admin)
        db.add(user)
        db.commit()
        print(f"Usuario administrador creado: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
