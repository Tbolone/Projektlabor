from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from src.database.db import get_db
from src.models.models import User


SECRET_KEY = os.getenv("SECRET_KEY", "fejlesztoi_titkos_kulcs_a_jwt_tokenhez_valtoztasd_meg")
ALGORITHM = "HS256"

# tokenUrl a bejelentkező végpont elérési útja
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Érvénytelen token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Érvénytelen token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Felhasználó nem található")
    return user