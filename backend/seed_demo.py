import sys
from datetime import date, datetime, timedelta, timezone

from src.database.db import SessionLocal
from src.models.models import (
    Contact,
    Courier,
    Package,
    PackageEvent,
    PackageStatus,
    User,
    UserType,
)
from src.services.auth_service import hash_password

ADMIN = ("admin@test.hu", "admin", "Admin Aladár")
COURIER = ("futar@test.hu", "futar", "Futár Ferenc")
COURIER2 = ("futar2@test.hu", "futar", "Futár Franciska")
CUSTOMER = ("reguser@reguser.hu", "reguser", "Regisztrált Róbert")


def get_or_create_user(db, email, password, name, user_type):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.password_hash = hash_password(password)
        user.type = user_type
        user.name = name
        return user

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        type=user_type,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_courier(db, user, plate, capacity):
    courier = db.query(Courier).filter(Courier.user_id == user.user_id).first()
    if courier:
        return courier

    courier = Courier(
        user_id=user.user_id,
        is_available=True,
        max_capacity=capacity,
        vehicle_plate_number=plate,
    )
    db.add(courier)
    db.flush()
    return courier


def make_contact(db, name, zip_code, city, street, email, phone, comment=None):
    contact = Contact(
        name=name,
        zip_code=zip_code,
        city=city,
        street_address=street,
        email=email,
        phone=phone,
        comment=comment,
    )
    db.add(contact)
    db.flush()
    return contact


def make_package(
    db,
    *,
    actor,
    pickup,
    delivery,
    size,
    weight,
    pickup_date,
    slot,
    status,
    pickup_courier=None,
    delivery_courier=None,
    sender=None,
    history=None,
):
    package = Package(
        pickup_contact_id=pickup.id,
        delivery_contact_id=delivery.id,
        sender_id=sender.user_id if sender else None,
        size=size,
        weight=weight,
        pickup_date=pickup_date,
        pickup_time_slot=slot,
        current_status=status,
        pickup_courier_id=pickup_courier.id if pickup_courier else None,
        delivery_courier_id=delivery_courier.id if delivery_courier else None,
    )
    db.add(package)
    db.flush()

    for event_status, hours_ago, courier in history or []:
        db.add(
            PackageEvent(
                package_id=package.id,
                actor_id=actor.user_id,
                courier_id=courier.id if courier else None,
                status=event_status,
                timestamp=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
                comment=None,
            )
        )

    return package


def reset_packages(db):
    db.query(PackageEvent).delete()
    db.query(Package).delete()
    db.query(Contact).delete()
    db.commit()
    print("A korábbi demó csomagok törölve.")


def main():
    reset = "--reset" in sys.argv
    db = SessionLocal()
    try:
        if reset:
            reset_packages(db)

        admin = get_or_create_user(db, ADMIN[0], ADMIN[1], ADMIN[2], UserType.ADMIN)
        courier_user = get_or_create_user(
            db, COURIER[0], COURIER[1], COURIER[2], UserType.DELIVERY_MAN
        )
        courier_user2 = get_or_create_user(
            db, COURIER2[0], COURIER2[1], COURIER2[2], UserType.DELIVERY_MAN
        )
        customer = get_or_create_user(
            db, CUSTOMER[0], CUSTOMER[1], CUSTOMER[2], UserType.REGISTERED_CUSTOMER
        )
        db.flush()

        courier = get_or_create_courier(db, courier_user, "ABC-123", 250.0)
        courier2 = get_or_create_courier(db, courier_user2, "XYZ-789", 180.0)
        db.commit()

        if db.query(Package).count() > 0:
            print("Már vannak csomagok az adatbázisban, a demó csomagok kimaradnak.")
            print_summary(db)
            return

        today = date.today()

        depot = make_contact(
            db, "Pagyar Mosta Raktár", "1097", "Budapest", "Gyáli út 12.",
            "raktar@pagyarmosta.hu", "+36 1 555 0100",
        )

        p1_from = make_contact(db, "Kiss Anna", "1051", "Budapest", "Arany János u. 4.",
                               "kiss.anna@example.com", "+36 30 111 2222")
        p1_to = make_contact(db, "Nagy Béla", "4025", "Debrecen", "Piac u. 20.",
                             "nagy.bela@example.com", "+36 30 333 4444")
        make_package(
            db, actor=customer, pickup=p1_from, delivery=p1_to, size="M", weight=3.5,
            pickup_date=today + timedelta(days=2), slot="08:00-12:00",
            status=PackageStatus.CREATED, sender=customer,
            history=[(PackageStatus.CREATED, 30, None)],
        )

        p2_from = make_contact(db, "Tóth Gábor", "6720", "Szeged", "Kárász u. 9.",
                               "toth.gabor@example.com", "+36 20 555 6666")
        p2_to = make_contact(db, "Szabó Edit", "9022", "Győr", "Baross út 3.",
                             "szabo.edit@example.com", "+36 20 777 8888")
        make_package(
            db, actor=admin, pickup=p2_from, delivery=p2_to, size="S", weight=1.2,
            pickup_date=today, slot="12:00-16:00",
            status=PackageStatus.ASSIGNED_FOR_PICKUP, pickup_courier=courier,
            sender=customer,
            history=[
                (PackageStatus.CREATED, 26, None),
                (PackageStatus.ASSIGNED_FOR_PICKUP, 5, courier),
            ],
        )

        p3_from = make_contact(db, "Varga Péter", "7621", "Pécs", "Király u. 15.",
                               "varga.peter@example.com", "+36 70 123 4567")
        p3_to = make_contact(db, "Kovács Lilla", "3525", "Miskolc", "Széchenyi u. 40.",
                             "kovacs.lilla@example.com", "+36 70 234 5678")
        make_package(
            db, actor=admin, pickup=p3_from, delivery=p3_to, size="L", weight=12.0,
            pickup_date=today, slot="08:00-12:00",
            status=PackageStatus.OUT_FOR_PICKUP, pickup_courier=courier,
            history=[
                (PackageStatus.CREATED, 50, None),
                (PackageStatus.ASSIGNED_FOR_PICKUP, 8, courier),
                (PackageStatus.OUT_FOR_PICKUP, 2, courier),
            ],
        )

        p4_from = make_contact(db, "Horváth Imre", "8200", "Veszprém", "Kossuth u. 7.",
                               "horvath.imre@example.com", "+36 30 987 6543")
        p4_to = make_contact(db, "Fehér Mónika", "1134", "Budapest", "Váci út 50.",
                             "feher.monika@example.com", "+36 30 876 5432")
        make_package(
            db, actor=admin, pickup=p4_from, delivery=p4_to, size="M", weight=5.4,
            pickup_date=today - timedelta(days=1), slot="12:00-16:00",
            status=PackageStatus.IN_WAREHOUSE, pickup_courier=courier,
            history=[
                (PackageStatus.CREATED, 80, None),
                (PackageStatus.ASSIGNED_FOR_PICKUP, 40, courier),
                (PackageStatus.OUT_FOR_PICKUP, 30, courier),
                (PackageStatus.PICKED_UP, 28, courier),
                (PackageStatus.IN_WAREHOUSE, 26, courier),
            ],
        )

        p5_from = make_contact(db, "Balogh Zsolt", "2400", "Dunaújváros", "Vasmű út 2.",
                               "balogh.zsolt@example.com", "+36 20 345 6789")
        p5_to = make_contact(db, "Molnár Eszter", "1026", "Budapest", "Pasaréti út 8.",
                             "molnar.eszter@example.com", "+36 20 456 7890")
        make_package(
            db, actor=admin, pickup=p5_from, delivery=p5_to, size="S", weight=2.1,
            pickup_date=today - timedelta(days=2), slot="08:00-12:00",
            status=PackageStatus.ASSIGNED_FOR_DELIVERY,
            pickup_courier=courier2, delivery_courier=courier, sender=customer,
            history=[
                (PackageStatus.CREATED, 100, None),
                (PackageStatus.ASSIGNED_FOR_PICKUP, 70, courier2),
                (PackageStatus.OUT_FOR_PICKUP, 60, courier2),
                (PackageStatus.PICKED_UP, 58, courier2),
                (PackageStatus.IN_WAREHOUSE, 55, courier2),
                (PackageStatus.ASSIGNED_FOR_DELIVERY, 4, courier),
            ],
        )

        p6_from = make_contact(db, "Simon Károly", "5000", "Szolnok", "Ady Endre út 11.",
                               "simon.karoly@example.com", "+36 70 567 8901")
        p6_to = make_contact(db, "Papp Júlia", "1114", "Budapest", "Bartók Béla út 60.",
                             "papp.julia@example.com", "+36 70 678 9012")
        make_package(
            db, actor=admin, pickup=p6_from, delivery=p6_to, size="M", weight=7.8,
            pickup_date=today - timedelta(days=2), slot="12:00-16:00",
            status=PackageStatus.OUT_FOR_DELIVERY,
            pickup_courier=courier, delivery_courier=courier,
            history=[
                (PackageStatus.CREATED, 120, None),
                (PackageStatus.ASSIGNED_FOR_PICKUP, 90, courier),
                (PackageStatus.OUT_FOR_PICKUP, 80, courier),
                (PackageStatus.PICKED_UP, 78, courier),
                (PackageStatus.IN_WAREHOUSE, 74, courier),
                (PackageStatus.ASSIGNED_FOR_DELIVERY, 10, courier),
                (PackageStatus.OUT_FOR_DELIVERY, 1, courier),
            ],
        )

        for index, (hours_pick, hours_deliver, who) in enumerate(
            [(74, 50, courier), (60, 36, courier), (48, 20, courier2)], start=7
        ):
            src = make_contact(db, f"Feladó {index}", "1011", "Budapest",
                               f"Fő utca {index}.", f"felado{index}@example.com",
                               "+36 1 222 3333")
            dst = make_contact(db, f"Címzett {index}", "7100", "Szekszárd",
                               f"Béla tér {index}.", f"cimzett{index}@example.com",
                               "+36 1 444 5555")
            make_package(
                db, actor=admin, pickup=src, delivery=dst, size="M", weight=4.0 + index,
                pickup_date=today - timedelta(days=4), slot="08:00-12:00",
                status=PackageStatus.DELIVERED,
                pickup_courier=who, delivery_courier=who, sender=customer,
                history=[
                    (PackageStatus.CREATED, hours_pick + 20, None),
                    (PackageStatus.ASSIGNED_FOR_PICKUP, hours_pick + 5, who),
                    (PackageStatus.OUT_FOR_PICKUP, hours_pick + 1, who),
                    (PackageStatus.PICKED_UP, hours_pick, who),
                    (PackageStatus.IN_WAREHOUSE, hours_pick - 3, who),
                    (PackageStatus.ASSIGNED_FOR_DELIVERY, hours_deliver + 4, who),
                    (PackageStatus.OUT_FOR_DELIVERY, hours_deliver + 1, who),
                    (PackageStatus.DELIVERED, hours_deliver, who),
                ],
            )

        p10_from = make_contact(db, "Lakatos Dóra", "2100", "Gödöllő", "Szabadság tér 5.",
                                "lakatos.dora@example.com", "+36 30 765 4321")
        p10_to = make_contact(db, "Fodor Tamás", "2030", "Érd", "Budai út 30.",
                              "fodor.tamas@example.com", "+36 30 654 3210")
        make_package(
            db, actor=admin, pickup=p10_from, delivery=p10_to, size="L", weight=15.5,
            pickup_date=today - timedelta(days=3), slot="16:00-20:00",
            status=PackageStatus.FAILED_DELIVERY,
            pickup_courier=courier2, delivery_courier=courier2,
            history=[
                (PackageStatus.CREATED, 96, None),
                (PackageStatus.ASSIGNED_FOR_PICKUP, 80, courier2),
                (PackageStatus.OUT_FOR_PICKUP, 72, courier2),
                (PackageStatus.PICKED_UP, 70, courier2),
                (PackageStatus.IN_WAREHOUSE, 68, courier2),
                (PackageStatus.ASSIGNED_FOR_DELIVERY, 30, courier2),
                (PackageStatus.OUT_FOR_DELIVERY, 26, courier2),
                (PackageStatus.FAILED_DELIVERY, 24, courier2),
            ],
        )

        db.commit()
        print_summary(db)

    finally:
        db.close()


def print_summary(db):
    print("\nDemó adatok készen állnak.")
    print(f"  Felhasználók: {db.query(User).count()}")
    print(f"  Futárok:      {db.query(Courier).count()}")
    print(f"  Csomagok:     {db.query(Package).count()}")
    print("\nBelépések:")
    print(f"  Admin:   {ADMIN[0]} / {ADMIN[1]}")
    print(f"  Futár:   {COURIER[0]} / {COURIER[1]}")
    print(f"  Futár 2: {COURIER2[0]} / {COURIER2[1]}")
    print(f"  Ügyfél:  {CUSTOMER[0]} / {CUSTOMER[1]}")


if __name__ == "__main__":
    main()
