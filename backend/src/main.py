"""FastAPI application entry point."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from infrastructure.config import settings
from api.auth_routes import router as auth_router
from api.self_routes import router as self_router
from api.subtitle_routes import router as subtitle_router
from api.upload_routes import router as upload_router
from api.dependencies import init_connections, close_connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("Starting application...")
    await init_connections()
    yield
    # Shutdown
    print("Shutting down application...")
    await close_connections()


# Create FastAPI application
app = FastAPI(
    title="Subtitles Search API",
    version="1.5.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Frontend static file serving
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
FRONTEND_DIST = os.path.join(FRONTEND_DIR, "dist")

# Serve static assets from frontend/dist if it exists, otherwise from frontend
if os.path.isdir(FRONTEND_DIST):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST, html=False), name="static")
elif os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=False), name="static")


# Include routers
app.include_router(subtitle_router)  # Subtitle endpoints (no prefix, match original API)
app.include_router(upload_router)  # Upload endpoints (no prefix, match original API)
app.include_router(auth_router)
app.include_router(self_router)


@app.get("/")
async def root():
    """Root endpoint - serve frontend SPA."""
    # Prefer built index.html from Vite (frontend/dist) when available
    if os.path.isfile(os.path.join(FRONTEND_DIST, "index.html")):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    # Fallback to development/static index.html
    if os.path.isfile(os.path.join(FRONTEND_DIR, "index.html")):
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    return {
        "message": "Subtitles Search API",
        "version": "1.5.0",
        "database": settings.DATABASE_TYPE,
        "docs": "/api/docs"
    }


@app.get("/content")
async def spa_content():
    """Serve SPA for /content route."""
    return await root()


@app.get("/admin")
async def spa_admin():
    """Serve SPA for /admin route."""
    return await root()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": settings.DATABASE_TYPE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
