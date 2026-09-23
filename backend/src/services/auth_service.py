import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models.user import User
from repositories import user_repository

SECRET_KEY = os.getenv("SECRET_KEY", "fejlesztoi_titkos_kulcs_a_jwt_tokenhez_valtoztasd_meg")
ALGORITHM = "HS256"

class EmailAlreadyUsedError(Exception):
    """Akkor dobjuk, ha a megadott email címmel már létezik felhasználó."""

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def register_user(db: Session, email: str, name: str, password: str) -> User:
    """Létrehoz egy új felhasználót, ha az email cím még szabad."""
    if user_repository.get_user_by_email(db, email):
        raise EmailAlreadyUsedError()

    try:
        return user_repository.create_user(db, email, name, hash_password(password))
    except IntegrityError:
        # Ha két regisztráció fut egyszerre, az adatbázis unique megszorítása fog.
        db.rollback()
        raise EmailAlreadyUsedError()

def authenticate_user(db: Session, email: str, password: str):
    """Ellenőrzi a jelszót és tokent generál, ha sikeres."""
    # 1. Lekérdezzük a repository-ból a usert
    user = user_repository.get_user_by_email(db, email)
    
    # 2. Ellenőrizzük a jelszót
    if not user or not verify_password(password, user.password_hash):
        return None
        
    # 3. Token generálása
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    token_data = {"sub": user.email, "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return token