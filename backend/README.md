# Backend

FastAPI + SQLAlchemy + PostgreSQL.

## Futtatás

1. Adatbázis indítása (a repo gyökeréből):

   ```bash
   docker compose up -d
   ```

2. Backend indítása (a `backend` mappából):

   ```bash
   uv run backend
   ```

   Az API a http://127.0.0.1:8000 címen fut, a Swagger dokumentáció a http://127.0.0.1:8000/docs címen érhető el.

## Környezeti változók

| Változó        | Alapérték                                          |
|----------------|----------------------------------------------------|
| `DATABASE_URL` | `postgresql://admin:pass@localhost:5432/database`  |
| `SECRET_KEY`   | fejlesztői kulcs – élesben kötelező felülírni      |
