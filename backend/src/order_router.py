from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from schemas.order import OrderCreateRequest
from services.order_service import OrderService
router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", summary="Új csomagfelvétel rögzítése")
def create_new_order(
    order_data: OrderCreateRequest, 
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user) # Ide jöhet a JWT auth user függőség
):
    
    try:
        current_user_id = 1  
        
        result = OrderService.create_order(db=db, order_data=order_data, current_user_id=current_user_id)
        return result
    except Exception as e:
        db.rollback()
        print(f"HIBA TÖRTÉNT A MENTÉS SORÁN: setError: {str(e)}")
        raise HTTPException(status_code=400, detail=f"setError: {str(e)}")