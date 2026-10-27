import uvicorn
from fastapi import FastAPI

from src import admin_router, auth_router, courier_router, user_router
from src.models import models


app = FastAPI(title="Projekt Backend API")

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(courier_router.router)
app.include_router(admin_router.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "API fut!"}

def run():
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    run()
