import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.seed import seed_roles_and_permissions
from app.api.v1.api import api_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("shuleconnect")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure base roles, permissions and plans are seeded
    logger.info("Initializing ShuleConnect SaaS backend...")
    db = SessionLocal()
    try:
        seed_roles_and_permissions(db)
        logger.info("Database roles, permissions, and initial plans verified.")
    except Exception as e:
        logger.warning(f"Seed step encountered: {e}")
    finally:
        db.close()
    yield
    # Shutdown
    logger.info("Shutting down ShuleConnect backend.")


app = FastAPI(
    title="ShuleConnect API",
    description="Production-Oriented Education Communication SaaS in Tanzania (Primary & Secondary Schools)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount versioned API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "ShuleConnect Backend API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
