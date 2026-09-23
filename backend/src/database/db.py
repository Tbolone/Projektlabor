import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Lokálisan localhost, Dockerben a DATABASE_URL env változóval felülírható
# (pl. postgresql://admin:pass@postgres_db:5432/database)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://admin:pass@localhost:5432/database"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
