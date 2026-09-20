from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://admin:pass@localhost:5432/database"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Generátor a biztonságos adatbázis-munkamenet (session) kezeléshez."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()