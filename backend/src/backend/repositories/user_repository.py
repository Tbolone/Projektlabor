from sqlalchemy.orm import Session
from backend.models.user import User

def get_user_by_email(db: Session, email: str) -> User | None:
    """Kikeresi a felhasználót az adatbázisból email alapján."""
    return db.query(User).filter(User.email == email).first()