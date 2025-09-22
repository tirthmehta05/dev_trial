from fastapi import FastAPI
from .app.controllers import config_controller

app = FastAPI(title="Dynamic Configuration API")

app.include_router(config_controller.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Dynamic Configuration API"}
