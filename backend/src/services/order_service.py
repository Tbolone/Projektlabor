import uuid
from sqlalchemy.orm import Session
from models.models import Contact, Package, User

class OrderService:
    @staticmethod
    def create_order(db: Session, order_data: OrderCreateRequest, current_user_id: int):
        # 1. Feladó kontakt mentése a CONTACTS táblába
        sender_contact = Contact(
            name=order_data.sender.name,
            email=order_data.sender.email,
            phone=order_data.sender.phone,
            zip_code=order_data.sender.zip,        # Frontend 'zip' -> DB 'zip_code'
            city=order_data.sender.city,
            street_address=order_data.sender.street  # Frontend 'street' -> DB 'street_address'
        )
        db.add(sender_contact)
        db.flush()  # ID generálásához

        # 2. Címzett kontakt mentése a CONTACTS táblába (mivel a delivery_contact_id kötelező a packages táblában)
        receiver_contact = Contact(
            name=order_data.receiver.name,
            email=order_data.receiver.email,
            phone=order_data.receiver.phone,
            zip_code=order_data.receiver.zip,        # Frontend 'zip' -> DB 'zip_code'
            city=order_data.receiver.city,
            street_address=order_data.receiver.street  # Frontend 'street' -> DB 'street_address'
        )
        db.add(receiver_contact)
        db.flush()

        # 3. Csomag (PACKAGE) mentése a PACKAGES táblába
        new_package = Package(
            tracking_id=uuid.uuid4(),
            pickup_contact_id=sender_contact.id,
            delivery_contact_id=receiver_contact.id,  # A modell alapján kötelező mező
            sender_id=current_user_id,   # A User modellben a PK 'user_id'
            receiver_id=None,
            size=order_data.package.size,
            weight=order_data.package.weight,
            pickup_date=order_data.package.pickup_date,
            pickup_time_slot=order_data.package.pickup_time_slot,
        )
        
        db.add(new_package)
        db.commit()
        db.refresh(new_package)

        return {
            "message": "Csomag sikeresen rögzítve!",
            "tracking_id": str(new_package.tracking_id),
            "package_id": new_package.id
        }