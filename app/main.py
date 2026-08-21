from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.models import Venue, Package, Payment, WifiSession, User
from app.routers import venues, packages, payments, portal, auth, dashboard

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0"
)

# ======================
# CORS Configuration
# ======================
origins = [
    "http://localhost:3000",      # React / Next.js local
    "http://localhost:5173",      # Vite
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # Add your future frontend domain here later
    # "https://app.hotspotpay.co.ke",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not settings.DEBUG else ["*"],  # allow all in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# Routers
# ======================
app.include_router(auth.router, prefix="/api/v1")
app.include_router(venues.router, prefix="/api/v1")
app.include_router(packages.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(portal.router)   # public captive portal


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "status": "running",
        "version": "0.1.0",
        "environment": "development" if settings.DEBUG else "production"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}