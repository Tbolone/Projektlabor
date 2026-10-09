import uvicorn
from fastapi import FastAPI

from src.models import models  # noqa: F401  (a modellek regisztrálása a Base-en)
from src import auth_router

app = FastAPI(title="Projekt Backend API")

# Routerek becsatolása
app.include_router(auth_router.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "API fut!"}

def run():
    # Itt is fontos a "src.main:app", különben az uvicorn nem találja meg a main.py-t!
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    run()