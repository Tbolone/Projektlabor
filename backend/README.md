# Backend

FastAPI + SQLAlchemy + PostgreSQL.

A teljes rendszert (adatbázis + backend + frontend) a repo gyökerében lévő
`start.ps1` / `start.sh` indítja. Ez a leírás csak a backend külön indításáról szól.

## Futtatás

1. Adatbázis indítása (a repo gyökeréből):

   ```bash
   docker compose up -d postgres_db
   ```

2. Backend indítása (a `backend` mappából):

   ```bash
   uv run uvicorn main:app --app-dir src --reload
   ```

   Az API a http://127.0.0.1:8000 címen fut, a Swagger dokumentáció a
   http://127.0.0.1:8000/docs címen érhető el.

Ha csak a backendet akarod a teljes indítóval elindítani:

```bash
.\start.ps1 -BackendOnly     # Windows
./start.sh --backend-only    # Linux / macOS
```

## Környezeti változók

| Változó        | Alapérték                                         |
|----------------|---------------------------------------------------|
| `DATABASE_URL` | `postgresql://admin:pass@localhost:5432/database` |
| `SECRET_KEY`   | fejlesztői kulcs – élesben kötelező felülírni     |

Az értékeket a repo gyökerében lévő `.env` fájl tartalmazza, az indítószkriptek
onnan olvassák ki őket.

## Szerkezet

A forrás a `src/` alatt lapos modulokban van (`main.py`, `auth_router.py`,
`database/`, `models/`, `repositories/`, `schemas/`, `services/`). A projekt nem
települ csomagként (`[tool.uv] package = false`), ezért az indításnál kell a
`--app-dir src` kapcsoló.

## Végpontok

| Metódus | Útvonal              | Leírás                                          |
|---------|----------------------|-------------------------------------------------|
| `GET`   | `/`                  | állapotjelzés                                   |
| `POST`  | `/api/auth/register` | regisztráció (`email`, `name`, `password`)      |
| `POST`  | `/api/auth/login`    | bejelentkezés, JWT tokent ad vissza             |

A regisztráció `201`-et ad sikeres esetben, `409`-et ha az email cím foglalt, és
`422`-t érvénytelen adatra (hibás email, 6 karakternél rövidebb jelszó).
