from sqlalchemy.orm import Session
from src.models.models import User, UserType

def get_user_by_email(db: Session, email: str) -> User | None:
    """Kikeresi a felhasználót az adatbázisból email alapján."""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, name: str, password_hash: str) -> User:
    """Létrehoz egy új regisztrált felhasználót."""
    user = User(
        email=email,
        name=name,
        password_hash=password_hash,
        type=UserType.REGISTERED_CUSTOMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
