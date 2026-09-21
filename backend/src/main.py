from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

import models.user  # noqa: F401  (a modell regisztrálása a Base-en)
import auth_router
from database.db import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Táblák létrehozása induláskor
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Projekt Backend API", lifespan=lifespan)

# Routerek becsatolása
app.include_router(auth_router.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "API fut!"}


def run():
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    run()



