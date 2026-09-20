import uuid
from sqlalchemy.orm import Session
from models import Package, PackageStatus, RoleEnum, User

def create_package(db: Session, recipient_email: str, size: str, pickup_address: str, delivery_address: str, sender_id: int = None, time_slot: str = None) -> Package:
    """Új csomag előjegyzése (vendég és regisztrált felhasználó is hívhatja)."""
    tracking_code = f"GLS-{str(uuid.uuid4())[:8].upper()}"
    new_package = Package(
        tracking_code=tracking_code,
        sender_id=sender_id,
        recipient_email=recipient_email,
        size=size,
        pickup_address=pickup_address,
        delivery_address=delivery_address,
        time_slot=time_slot
    )
    db.add(new_package)
    db.commit()
    db.refresh(new_package)
    return new_package

def assign_pickup_courier(db: Session, package_id: int, courier_id: int, requesting_user: User) -> Package:
    """A logisztikus kiosztja a felvételi feladatot egy futárnak."""
    if requesting_user.role not in [RoleEnum.LOGISTICS, RoleEnum.ADMIN]:
        raise PermissionError("Csak logisztikus vagy admin oszthat ki futárt.")
    
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise ValueError("A csomag nem található.")
    
    if package.status != PackageStatus.REGISTERED:
        raise ValueError("Csak előjegyzett csomaghoz rendelhető felvételi futár.")
        
    package.pickup_courier_id = courier_id
    package.status = PackageStatus.ASSIGNED_FOR_PICKUP
    db.commit()
    db.refresh(package)
    return package

def update_package_status_by_courier(db: Session, package_id: int, new_status: PackageStatus, courier_user: User) -> Package:
    """A futár státuszt vált (pl. felvette a csomagot)."""
    if courier_user.role != RoleEnum.COURIER:
        raise PermissionError("Ezt a műveletet csak futár végezheti.")
        
    package = db.query(Package).filter(Package.id == package_id).first()

    if package.pickup_courier_id != courier_user.id and package.delivery_courier_id != courier_user.id:
        raise PermissionError("Ez a csomag nincs hozzád rendelve.")
        
    package.status = new_status
    db.commit()
    db.refresh(package)
    return package