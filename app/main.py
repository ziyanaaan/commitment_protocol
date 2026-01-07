from fastapi import FastAPI
from app.services.scheduler import start_scheduler

app= FastAPI()


@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.get("/")
def health():
    return {"status": "ok"}
