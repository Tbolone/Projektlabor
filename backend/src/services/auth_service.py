import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.models.models import User
from src.repositories import user_repository
from src.deps import SECRET_KEY, ALGORITHM


class EmailAlreadyUsedError(Exception):
    pass

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def register_user(db: Session, email: str, name: str, password: str) -> User:
    if user_repository.get_user_by_email(db, email):
        raise EmailAlreadyUsedError()

    try:
        return user_repository.create_user(db, email, name, hash_password(password))
    except IntegrityError:
        db.rollback()
        raise EmailAlreadyUsedError()


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        return None

    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    token_data = {"sub": user.email, "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return token
