from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from schemas.order import OrderCreateRequest, PackageResponseSchema
from services.order_service import OrderService
from typing import List
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


@router.get("/", response_model=List[PackageResponseSchema], summary="Összes csomag listázása")
def get_packages(db: Session = Depends(get_db)):
    try:
        packages = OrderService.get_all_packages(db)
        return packages
    except Exception as e:
        print(f"setError: {str(e)}")
        raise HTTPException(status_code=400, detail=f"setError: {str(e)}")

@router.get("/{package_id}", response_model=PackageResponseSchema, summary="Egyedi csomag lekérdezése ID alapján")
def get_package_details(package_id: int, db: Session = Depends(get_db)):
    try:
        package = OrderService.get_package_by_id(db=db, package_id=package_id)
        return package
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"setError: {str(e)}")
        raise HTTPException(status_code=400, detail=f"setError: {str(e)}")