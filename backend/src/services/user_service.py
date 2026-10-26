from sqlalchemy.orm import Session
from src.models.models import User

def get_user_list(db: Session):

    users = db.query(User).all()

    return users
