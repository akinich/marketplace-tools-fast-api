"""
================================================================================
Farm Management System - FastAPI Main Application
================================================================================
Version: 1.1.0
Last Updated: 2025-11-18

Changelog:
----------
v1.1.0 (2025-11-18):
  - Added background scheduler for inventory reservation auto-expiry
  - Integrated APScheduler into lifespan management
  - Enhanced health check with scheduler status

v1.0.0 (2025-11-17):
  - Initial FastAPI application setup
  - CORS middleware configuration
  - Database connection lifecycle
  - Health check endpoints
  - API router mounting
  - Activity logging middleware
  - Error handling

================================================================================
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
from typing import Any

from app.config import settings, display_settings
from app.database import connect_db, disconnect_db, check_database_health
from app.scheduler import start_scheduler, stop_scheduler, get_scheduler_status

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events (startup and shutdown).
    """
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("🚀 Starting Farm Management System API...")
    display_settings()

    try:
        # Connect to database
        await connect_db()

        # Start background scheduler
        start_scheduler()

        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

    yield

    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("👋 Shutting down Farm Management System API...")

    # Stop background scheduler
    stop_scheduler()

    # Disconnect from database
    await disconnect_db()

    logger.info("✅ Shutdown complete")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI backend for Farm Management System - Inventory, Biofloc, and more",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests with timing information.
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log request details
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )

    # Add custom header with response time
    response.headers["X-Process-Time"] = str(duration)

    return response


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors with detailed messages.
    """
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# ============================================================================
# ROOT & HEALTH CHECK ENDPOINTS
# ============================================================================


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint - verify all services are operational.
    """
    db_healthy = await check_database_health()
    scheduler_status = get_scheduler_status()

    return {
        "status": "healthy" if db_healthy and scheduler_status["status"] == "running" else "unhealthy",
        "services": {
            "api": "operational",
            "database": "operational" if db_healthy else "down",
            "scheduler": scheduler_status["status"],
        },
        "scheduled_jobs": scheduler_status.get("jobs", []),
        "version": settings.API_VERSION,
        "environment": settings.APP_ENV,
    }


@app.get("/ping", tags=["Health"])
async def ping():
    """
    Simple ping endpoint for quick uptime checks.
    """
    return {"message": "pong"}


# ============================================================================
# API ROUTERS
# ============================================================================

# Import routers
from app.routes import auth, admin, inventory, dashboard

# Mount routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(admin.router, prefix=f"{settings.API_PREFIX}/admin", tags=["Admin Panel"])
app.include_router(inventory.router, prefix=f"{settings.API_PREFIX}/inventory", tags=["Inventory"])
app.include_router(dashboard.router, prefix=f"{settings.API_PREFIX}/dashboard", tags=["Dashboard"])

# To be added later:
# from app.routes import biofloc
# app.include_router(biofloc.router, prefix=f"{settings.API_PREFIX}/biofloc", tags=["Biofloc"])


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
