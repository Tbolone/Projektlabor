import uuid
from datetime import date, timedelta

import httpx

c = httpx.Client(base_url="http://localhost:8000", timeout=15.0)
results = []


def check(label, actual, expected):
    results.append((actual == expected, label))
    print(f"{'OK  ' if actual == expected else 'HIBA'} {label}: {actual!r} (vart: {expected!r})")


def login(email, password):
    r = c.post("/api/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"} if r.status_code == 200 else None


suffix = uuid.uuid4().hex[:8]
admin = login("admin@test.hu", "admin")
courier_h = login("futar@test.hu", "futar")
check("admin belepes", admin is not None, True)
check("futar belepes", courier_h is not None, True)

print("\n--- raktaros letrehozasa es belepese ---")
check("raktaros letrehozasa", c.post("/api/admin/users", headers=admin, json={
    "name": f"Raktaros {suffix}", "email": f"raktaros_{suffix}@test.hu",
    "password": "raktar123", "type": "warehouse_staff"}).status_code, 201)
staff = login(f"raktaros_{suffix}@test.hu", "raktar123")
check("raktaros belepes", staff is not None, True)

cust_email = f"ugyfel_{suffix}@test.hu"
c.post("/api/auth/register", json={
    "email": cust_email, "name": "Teszt Ugyfel", "password": "jelszo123"})
customer = login(cust_email, "jelszo123")

r = c.post("/orders/", headers=customer, json={
    "sender": {"name": "Teszt Ugyfel", "email": cust_email, "phone": "+36301111111",
               "zip": "1011", "city": "Budapest", "street": "Fo utca 1."},
    "receiver": {"name": "Cimzett Cecil", "email": f"cimzett_{suffix}@test.hu",
                 "phone": "+36302222222", "zip": "4025", "city": "Debrecen",
                 "street": "Piac utca 2."},
    "package": {"size": "M", "weight": 4.5,
                "pickup_date": str(date.today() + timedelta(days=3)),
                "pickup_time_slot": "08:00-12:00"}})
check("csomagfeladas", r.status_code, 200)
package_id = r.json()["package_id"]

print("\n--- jogosultsagok ---")
check("raktaros latja a csomagokat", c.get("/api/warehouse/packages", headers=staff).status_code, 200)
check("ugyfel nem erheti el a raktarat", c.get("/api/warehouse/packages", headers=customer).status_code, 403)
check("bejelentkezes nelkul sem", c.get("/api/warehouse/packages").status_code, 401)
check("csomag reszletei esemenyekkel",
      "events" in c.get(f"/api/warehouse/packages/{package_id}", headers=staff).json(), True)

print("\n--- futarok es kiosztas ---")
couriers = c.get("/api/warehouse/couriers", headers=staff).json()
check("raktaros latja a futarokat", len(couriers) > 0, True)
check("terheltseg is latszik", "current_load" in couriers[0], True)

r = c.post(f"/api/warehouse/packages/{package_id}/assign", headers=staff,
           json={"courier_id": 1, "stage": "pickup"})
check("felveteli futar kijelolese", r.status_code, 200)
check("  allapot", r.json()["current_status"], "assigned_for_pickup")

print("\n--- az elindult futar nem helyezheto at ---")
c.post(f"/api/courier/packages/{package_id}/start-pickup", headers=courier_h, json={})
new_courier = c.post("/api/admin/couriers", headers=admin, json={
    "name": f"Uj Futar {suffix}", "email": f"ujfutar_{suffix}@test.hu",
    "password": "futar123", "max_capacity": 150,
    "vehicle_plate_number": f"UF-{suffix[:3]}"}).json()
check("elindult futar athelyezese TILOS",
      c.post(f"/api/warehouse/packages/{package_id}/assign", headers=staff,
             json={"courier_id": new_courier["id"], "stage": "pickup"}).status_code, 409)
check("az admin viszont athelyezheti",
      c.post(f"/api/admin/packages/{package_id}/assign", headers=admin,
             json={"courier_id": 1, "stage": "pickup"}).status_code, 200)

print("\n--- takaritas ---")
c.delete(f"/api/admin/couriers/{new_courier['id']}", headers=admin)
for email in (cust_email, f"raktaros_{suffix}@test.hu"):
    users = c.get(f"/api/admin/users?search={email}", headers=admin).json()
    if users:
        c.delete(f"/api/admin/users/{users[0]['user_id']}", headers=admin)

print()
failed = [label for ok, label in results if not ok]
print(f"OSSZESEN: {sum(1 for ok, _ in results if ok)} / {len(results)} rendben")
for label in failed:
    print("  HIBAS:", label)
