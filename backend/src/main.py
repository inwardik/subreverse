"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from infrastructure.config import settings
from api.routes import router
from api.auth_routes import router as auth_router
from api.self_routes import router as self_router
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
    title=settings.API_TITLE,
    version=settings.API_VERSION,
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


# Include routers
app.include_router(router)
app.include_router(auth_router)
app.include_router(self_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Pairs API",
        "version": settings.API_VERSION,
        "database": settings.DATABASE_TYPE,
        "docs": "/api/docs"
    }


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
