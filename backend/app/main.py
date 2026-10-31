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
    logger.info("Initializing ShuleHub SaaS backend...")
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
    logger.info("Shutting down ShuleHub backend.")


app = FastAPI(
    title="ShuleHub API",
    description="Production-Oriented Education Communication SaaS in Tanzania (Primary & Secondary Schools)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi import HTTPException

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
        "service": "ShuleHub Backend API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Frontend SPA and Static Assets Mounting
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "docs" or full_path.startswith("docs/") or full_path == "redoc":
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = FRONTEND_DIST / full_path
        if full_path and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", status_code=status.HTTP_200_OK, tags=["Health"])
    def root_status():
        return {
            "status": "online",
            "service": "ShuleHub Backend API",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": "/docs",
        }
