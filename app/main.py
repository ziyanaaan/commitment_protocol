from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.commitment import router as commitment_router
from app.api.delivery import router as delivery_router
from app.services.scheduler import start_scheduler
from app.api.preview import router as preview_router
from app.core.errors import value_error_handler
from app.api.payment import router as payment_router
from app.api.settlement import router as settlement_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.webhooks import router as webhook_router
from app.api.beneficiary import router as beneficiary_router
from fastapi.middleware.cors import CORSMiddleware

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Commitment Protocol API",
    description="Secure commitment protocol for client-freelancer agreements",
    version="1.0.0",
)

# Attach limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://commitment-protocol.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(ValueError, value_error_handler)

# Authentication routes (NEW)
app.include_router(auth_router)

# Existing routes (UNCHANGED)
app.include_router(commitment_router)
app.include_router(delivery_router)
app.include_router(preview_router)
app.include_router(payment_router)
app.include_router(settlement_router)

# Admin dashboard routes (NEW)
app.include_router(admin_router)

# Webhook routes (FINANCIAL INFRASTRUCTURE)
app.include_router(webhook_router)

# Beneficiary routes (PAYOUT ACCOUNTS)
app.include_router(beneficiary_router)



@app.on_event("startup")
def startup():
    start_scheduler()

@app.get("/")
def health():
    return {"status": "ok"}

