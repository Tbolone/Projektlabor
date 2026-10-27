from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from src.database.db import get_db
from src.models.models import User, UserType, Courier


SECRET_KEY = os.getenv("SECRET_KEY", "fejlesztoi_titkos_kulcs_a_jwt_tokenhez_valtoztasd_meg")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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


def require_roles(*allowed_types: UserType):
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if current_user.type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ehhez a művelethez nincs jogosultságod"
            )
        return current_user
    return dependency


require_admin = require_roles(UserType.ADMIN)
require_courier = require_roles(UserType.DELIVERY_MAN)
require_staff = require_roles(UserType.ADMIN, UserType.WAREHOUSE_STAFF)


def get_current_courier(
    current_user: Annotated[User, Depends(require_courier)],
    db: Annotated[Session, Depends(get_db)]
) -> Courier:
    courier = db.query(Courier).filter(Courier.user_id == current_user.user_id).first()
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ehhez a felhasználóhoz nem tartozik futár-profil"
        )
    return courier
