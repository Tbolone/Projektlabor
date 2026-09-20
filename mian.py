from backend.database import engine, Base, SessionLocal
import models
from auth_service import register_user
from models import RoleEnum

models.Base.metadata.create_all(bind=engine)

def initialize_database():
    db = SessionLocal()
    try:
        admin_exists = db.query(models.User).filter(models.User.email == "admin@gls.local").first()
        if not admin_exists:
            register_user(db, name="Fő Adminisztrátor", email="admin@gls.local", password="adminpassword", role=RoleEnum.ADMIN)
            print("Kezdeti Admin fiók létrehozva (admin@gls.local / adminpassword).")
        else:
            print("Az adatbázis már inicializálva van.")
    finally:
        db.close()

if __name__ == "__main__":
    print("Backend indítása és adatbázis szinkronizáció...")
    initialize_database()