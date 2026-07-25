from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseSettings
import logging
import importlib
from typing import List

# -----------------------
# Config
# -----------------------
class Settings(BaseSettings):
    APP_NAME: str = "Nexus Godzilla - Backend"
    DEBUG: bool = True
    ALLOWED_HOSTS: List[str] = ["*"]
    PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///./backend.db"
    MODEL_MODE: str = "local"  # 'local' or 'remote'
    MODEL_PATH: str = ""  # local quantized model path or repo id

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("nexus-backend")

# -----------------------
# App init
# -----------------------
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    description="Backend for Nexus Godzilla — FastAPI skeleton with conditional routers for modules.",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Error handlers
# -----------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error for request %s: %s", request.url, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# -----------------------
# Health & meta routes
# -----------------------
root_router = APIRouter()

@root_router.get("/", tags=["meta"])
async def read_root():
    return {"service": settings.APP_NAME, "status": "ok", "version": app.version}

@root_router.get("/health", tags=["meta"])
async def health_check():
    # Add DB / external service checks here if available
    return {"status": "healthy"}

app.include_router(root_router)

# -----------------------
# Conditional router loader
# -----------------------
def try_include_router(module_path: str, router_name: str = "router"):
    """
    Try to import module_path and attach attribute `router_name` (APIRouter) to app.
    Useful while scaffolding — modules may not exist yet.
    """
    try:
        module = importlib.import_module(module_path)
        router = getattr(module, router_name, None)
        if router:
            app.include_router(router)
            logger.info("Included router from %s", module_path)
        else:
            logger.warning("Module %s found but no '%s' attribute", module_path, router_name)
    except ModuleNotFoundError:
        logger.debug("Module %s not found (skipping).", module_path)
    except Exception:
        logger.exception("Error importing %s", module_path)

# Try to attach routers for the planned modules.
planned_modules = [
    "backend.freelancing.router",
]

for mod in planned_modules:
    try_include_router(mod)

# -----------------------
# Example placeholder endpoints (quick testing)
# -----------------------
example_router = APIRouter(prefix="/example", tags=["example"])

@example_router.get("/freelancing/sample")
async def sample_freelancing():
    return {"module": "freelancing", "message": "Create backend/freelancing/router.py to enable full routes."}

app.include_router(example_router)

# -----------------------
# Startup / Shutdown events
# -----------------------
@app.on_event("startup")
async def on_startup():
    logger.info("Starting %s", settings.APP_NAME)
    # Initialize DB, AI engine, scheduler, etc. here if/when implemented

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down %s", settings.APP_NAME)

# -----------------------
# Uvicorn entrypoint
# -----------------------
if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
