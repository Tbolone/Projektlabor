from sqlalchemy.orm import Session
from models.models import User
from repositories import user_repository
from services import auth_service

def get_user_list(db: Session):

    users = db.query(User).all()

    return users

class UserNotFoundError(Exception):
    pass
 
 
class InvalidCurrentPasswordError(Exception):
    pass
 
 
def update_profile(
    db: Session, user_id: int, name: str, primary_address: str | None
) -> User:
    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError
    return user_repository.update_user_profile(db, user, name, primary_address)
 
 
def change_password(
    db: Session, user_id: int, current_password: str, new_password: str
) -> None:
    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError
 
    if not user.password_hash or not auth_service.verify_password(
        current_password, user.password_hash
    ):
        raise InvalidCurrentPasswordError
 
    user_repository.update_user_password(
        db, user, auth_service.hash_password(new_password)
    )