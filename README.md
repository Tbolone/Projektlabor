# Projektlabor

Belsős dokumentáció:
https://miro.com/app/board/uXjVHk9bYOE=/?share_link_id=327701502505

## Indítás

Egy paranccsal elindul minden: frissülnek a függőségek, elindul az adatbázis,
a backend, végül a frontend.

**Windows (PowerShell):**

```powershell
.\start.ps1
```

**Linux / macOS:**

```bash
./start.sh
```

Kapcsolók:

| Windows         | Linux / macOS     | Mit csinál                                        |
|-----------------|-------------------|---------------------------------------------------|
| `-Fresh`        | `--fresh`         | minden függőséget újratelepít nulláról            |
| `-NoDocker`     | `--no-docker`     | Docker helyett helyi SQLite adatbázist használ    |
| `-BackendOnly`  | `--backend-only`  | csak a backendet indítja, frontend nélkül         |

Előfeltétel: [uv](https://docs.astral.sh/uv/) és futó Docker (az utóbbi
elhagyható a `--no-docker` kapcsolóval). A szkript kilépéskor leállítja a
backendet; az adatbázist a `docker compose down` állítja le.

A frontend bezárásával az egész leáll. A backend naplója a `.logs/` mappába kerül.


Entitások:
	- futár
	- raktár
	- csomag
	- felhasználó
		- vendég
		- regisztrált
		- futár
		- logisztikus
		- admin

Folyamat:
	- Rendelés létrehozása
	- Logisztikus kiosztja a csomagfelvételi feladatot egy futárnak
	- Futár felveszi a csomagot (rögzíti a rendszerben)
	- Csomag beérkezik a raktárba
		- Logisztikus leveszi a futárról a csomagot
	- Logisztikus kiosztja a csomagot a kiszállítást végző futárnak
	- Futár leadja a csomagot a megadott címen
	
Entitások kifejtve:
	Futár:
		Tulajdonságok:
			- Azonosító
			- Role
			- Név
			- Státusz (dolgozik, szabin van stb)
			- Terheltség (lehet-e még kiosztani rá csomagot)
			- Raktár
			- Felhasználónév
			- Jelszó
		
		Metódusok:
			- Csomagfelvétel
			- Csomagleadás
			- Saját szállítási történet megtekintése napi / heti / havi bontásban
			- Egyszerre több csomagot is kezelhet
			- Egyszerre tud akár kiszállítást és beszállítást is végezni
	Logisztikus:
		Tulajdonságok:
			- Azonosító
			- Role
			- Név
			- Raktár
			- Felhasználónév
			- Jelszó
			
		Metódusok:
			- Csomag érkeztetése a raktárba
			- Csomag kiosztása futárra
			- Csomag levétele futárról
			- Csomag kiosztás módosítása másik futárra / kézbesítés dátumának
  módosítása
			- Raktárban tárolt és futárhoz rendelt összes csomag megtekintése	
	Vendég felhasználó:
		Tulajdonságok:
			- Nincs?
			
		Metódusok:
			- Csomagfeldás
			- Csomagátvétel
			- Nyomonkövetés (aktuális státusz megjelenítése azonosító alapján)	
	Regisztrált felhasználó:
		Tulajdonságok:
			- Azonosító
			- Role
			- Felhasználónév
			- Email
			- Jelszó
	
		Metódusok:
			- Feladott és érkező csomagok nyomonkövetése (listázás)
			- Átvételi idősáv, szállítási cím, méret módosítása, legkésőbb a felvétel előtti
			  napig
	
	Admin:
		Tulajdonságok:
			- Azonosító
			- Role
			- Felhasználónév
			- Jelszó
			
		Metódusok:
			- Minden entitást lát (futár, logisztikus, felhasználó, csomag, raktár)
			- Módosíthatja az entitások adatait
			- Törölheti az entitásokat a rendszerből
			- Módosíthatja a csomagok futárhoz rendelését
			- Statisztikák megjelenítése egy raktár aktuális és historikus
kihasználtságáról, futárok által elvégzett szállításokról 
		
	Csomag:
		Tulajdonságok:
			- Címzett
			- Feladó
			- Súly
			- Fizetendő	
	Csomagstátuszok:
		- Futárnál (felvéve)
		- Raktárban
		- Futárnál (kiszállítás alatt)
		- Kiszállítva
		- Átvétel megtagadva
	Szerepkörök:
		- reg. felhasználó
		- admin
		- logisztikus
		- futár
		
Stack:
	- Python
	- GUI: CustomTkinter
	- SQLite --> egyetlen fájl, nem kell szerver
	- Deployment --> PyInstaller (tud exe-t és linux fájlt is buildelni)
	
Architektúra:
	- db.py --> adatbázis kapcsolat
	- models.py --> adatosztályok (Csomag, Futár, stb.)
	- services/ --> üzleti logika
	- gui/ --> login képernyő, külön frame-ek role-ok szerint)	
Táblák:
felhasznalo
Minden bejelentkezett szereplő (regisztrált küldő/címzett, futár, raktáros, admin). A vendég nem kap rekordot, ő csak a csomag denormalizált mezőin keresztül van jelen.

id PK
nev
email (unique)
jelszo_hash, telefonszam
szerepkor (enum)
letrehozva
csomag
A rendszer központi entitása.

id PK, azonosito (a nyilvános követőkód, unique)
feladas_felhasznalo_id FK (nullable, ha vendég adta fel)
feladasi_nev, feladasi_telefon, feladasi_email (mindig kitöltve, regisztrált félnél is)
cimzett_felhasznalo_id FK (nullable), cimzett_nev, cimzett_telefon, cimzett_email
felveteli_cim, kezbesitesi_cim, meret, suly
atveteli_idosav_kezdet, atveteli_idosav_veg, tervezett_felveteli_datum
statusz (előjegyezve / felvéve / raktáron / kiszállítás alatt / kézbesítve)
letrehozva
futar_hozzarendeles
Ezen a táblán keresztül köti a raktáros (vagy admin) a futárt a csomaghoz, külön a felvételi és a kiszállítási lépéshez.

id PK
csomag_id FK
futar_id FK
tipus (felvétel/kiszállítás)
hozzarendelte_id FK (ki jelölte ki – raktáros vagy admin)
hozzarendeles_idopontja, elinditva_idopontja, teljesitve_idopontja, statusz

A "miután elindult, nem módosítható" szabályt itt az elinditva_idopontja mező jelenléte jelzi – az üzleti logika réteg ez alapján tiltja le a módosítást (admin kivételével).

esemeny_naplo
Audit trail, ez adja a vendég/címzett követő oldalát, a regisztrált user előzményeit, és ebből számolható az admin statisztika (raktári kihasználtság, átlagos kiszállítási idő).

id PK
csomag_id FK
esemeny_tipus
idopont
rogzito_felhasznalo_id FK (nullable)
