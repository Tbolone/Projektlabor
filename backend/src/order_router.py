from fastapi import APIRouter, Depends, HTTPException
from models.models import User
from sqlalchemy.orm import Session
from database.db import get_db
from schemas.order import OrderCreateRequest
from services.order_service import OrderService
from deps import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", summary="Új csomagfelvétel rögzítése")
def create_new_order(
    order_data: OrderCreateRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return OrderService.create_order(
            db=db, order_data=order_data, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"HIBA TÖRTÉNT A MENTÉS SORÁN: setError: {str(e)}")
        raise HTTPException(status_code=400, detail=f"setError: {str(e)}")