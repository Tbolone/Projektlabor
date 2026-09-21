from fastapi import FastAPI
from backend.database.db import engine, Base
from backend.api import auth_router
import backend.models.user

# Táblák létrehozása induláskor
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Projekt Backend API")

# Routerek becsatolása
app.include_router(auth_router.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "API fut!"}