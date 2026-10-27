from getpass import getpass

from sqlalchemy.exc import IntegrityError

from src.database.db import SessionLocal
from src.models.models import User, UserType
from src.repositories.user_repository import get_user_by_email
from src.services.auth_service import hash_password


def main():
    name = input("Felhasználó neve: ").strip()
    email = input("Felhasználó e-mail-címe: ").strip().lower()
    print("Lehetséges felhasználó típusok:\n"
          "admin - 0\nregistered customer - 1\n"
          "unregistered customer - 2\n"
          "warehouse staff - 3\n"
          "delivery man - 4")

    while True:
        try:
            user_type_num = int(input("Felhasználó típusa (szám): ").strip())
        except ValueError:
            print("Kérlek, egy számot adj meg.")
            continue

        if user_type_num == 0:
            user_type = UserType.ADMIN
        elif user_type_num == 1:
            user_type = UserType.REGISTERED_CUSTOMER
        elif user_type_num == 2:
            user_type = UserType.UNREGISTERED_CUSTOMER
        elif user_type_num == 3:
            user_type = UserType.WAREHOUSE_STAFF
        elif user_type_num == 4:
            user_type = UserType.DELIVERY_MAN
        else:
            print("Nincs ilyen opció.")
            continue

        break

    if not name or not email:
        print("A név és az e-mail-cím megadása kötelező.")
        return

    password = getpass("Felhasználó jelszava: ")
    confirm = getpass("Jelszó újra: ")

    if not password:
        print("A jelszó nem lehet üres.")
        return

    if len(password.encode("utf-8")) > 72:
        print("A jelszó túl hosszú.")
        return

    if password != confirm:
        print("A két jelszó nem egyezik.")
        return

    db = SessionLocal()

    try:
        if get_user_by_email(db, email):
            print("Ezzel az e-mail-címmel már létezik felhasználó.")
            return

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            type=user_type
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"Felhasználó létrehozva: {user.email}")
        print(f"Felhasználóazonosító: {user.user_id}")
        print(f"Szerepkör: {user.type.value}")

    except IntegrityError:
        db.rollback()
        print("Az felhasználó létrehozása sikertelen; ellenőrizd, hogy létezik-e már ez az e-mail-cím.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
