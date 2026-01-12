from fastapi import FastAPI
from app.api.commitment import router as commitment_router
from app.api.delivery import router as delivery_router
from app.services.scheduler import start_scheduler
from app.api.preview import router as preview_router
from app.core.errors import value_error_handler
from app.api.payment import router as payment_router



app = FastAPI()

app.add_exception_handler(ValueError, value_error_handler)
app.include_router(commitment_router)
app.include_router(delivery_router)
app.include_router(preview_router)
app.include_router(payment_router)



@app.on_event("startup")
def startup():
    start_scheduler()

@app.get("/")
def health():
    return {"status": "ok"}
