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

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
 
 
def update_user_profile(
    db: Session, user: User, name: str, primary_address: str | None
) -> User:
    user.name = name
    user.primary_address = primary_address
    db.commit()
    db.refresh(user)
    return user
 
 
def update_user_password(db: Session, user: User, password_hash: str) -> None:
    user.password_hash = password_hash
    db.commit()