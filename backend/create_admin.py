
from getpass import getpass

from sqlalchemy.exc import IntegrityError

from src.database.db import SessionLocal
from src.models.models import User, UserType
from src.repositories.user_repository import get_user_by_email
from src.services.auth_service import hash_password


def main():
    name = input("Admin neve: ").strip()
    email = input("Admin e-mail-címe: ").strip().lower()

    if not name or not email:
        print("A név és az e-mail-cím megadása kötelező.")
        return

    password = getpass("Admin jelszava: ")
    confirm = getpass("Jelszó újra: ")

    if not password:
        print("A jelszó nem lehet üres.")
        return

    if len(password.encode("utf-8")) > 72:
        print("Túl hosszú jelszó.")
        return

    if password != confirm:
        print("A két jelszó nem egyezik.")
        return

    db = SessionLocal()

    try:
        if get_user_by_email(db, email):
            print("Ezzel az e-mail-címmel már létezik felhasználó.")
            return

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            type=UserType.ADMIN,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Admin felhasználó létrehozva: {admin.email}")
        print(f"Felhasználóazonosító: {admin.user_id}")
        print(f"Szerepkör: {admin.type.value}")

    except IntegrityError:
        db.rollback()
        print("Az admin létrehozása sikertelen; ellenőrizd, hogy létezik-e már ez az e-mail-cím.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
