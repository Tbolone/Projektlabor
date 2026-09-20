import bcrypt
from sqlalchemy.orm import Session
from models import User, RoleEnum

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(db: Session, name: str, email: str, password: str, role: RoleEnum = RoleEnum.CUSTOMER) -> User:
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Az email cím már foglalt.")
    
    new_user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def login_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Hibás email cím vagy jelszó.")
    return user