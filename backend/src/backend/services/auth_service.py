import bcrypt
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.repositories import user_repository

SECRET_KEY = "titkos_kulcs_a_jwt_tokenhez"
ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(db: Session, email: str, password: str):
    """Ellenőrzi a jelszót és tokent generál, ha sikeres."""
    # 1. Lekérdezzük a repository-ból a usert
    user = user_repository.get_user_by_email(db, email)
    
    # 2. Ellenőrizzük a jelszót
    if not user or not verify_password(password, user.password_hash):
        return None
        
    # 3. Token generálása
    expire = datetime.utcnow() + timedelta(hours=24)
    token_data = {"sub": user.email, "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return token