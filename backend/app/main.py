"""
FastAPI application entry point.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time

from app.config import settings
from app.database import engine, Base
from app.api import auth, invites, users, admin, posts, social, media
from app.core.exceptions import (
    InviteTreeException,
    InsufficientQuotaException,
    InvalidInviteTokenException,
    UnauthorizedException
)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Forensic-first invite tree system for tracking and pruning malicious networks",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting based on endpoint and client."""
    from app.core.rate_limit import AUTH_RATE_LIMIT, INVITE_RATE_LIMIT, ADMIN_RATE_LIMIT, DEFAULT_RATE_LIMIT
    
    path = request.url.path
    
    # Select appropriate rate limiter based on path
    if path.startswith("/api/auth/"):
        rate_limiter = AUTH_RATE_LIMIT
    elif path.startswith("/api/invites/"):
        rate_limiter = INVITE_RATE_LIMIT
    elif path.startswith("/api/admin/"):
        rate_limiter = ADMIN_RATE_LIMIT
    else:
        rate_limiter = DEFAULT_RATE_LIMIT
    
    return await rate_limiter(request, call_next)


# Exception handlers
@app.exception_handler(InsufficientQuotaException)
async def insufficient_quota_handler(request: Request, exc: InsufficientQuotaException):
    """Handle insufficient quota exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "INSUFFICIENT_QUOTA",
                "message": str(exc)
            }
        }
    )


@app.exception_handler(InvalidInviteTokenException)
async def invalid_token_handler(request: Request, exc: InvalidInviteTokenException):
    """Handle invalid invite token exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "INVALID_INVITE_TOKEN",
                "message": str(exc)
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors()
            }
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(invites.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(posts.router)
app.include_router(social.router)
app.include_router(media.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # In development, you can auto-create tables
    # In production, use Alembic migrations
    if settings.DEBUG:
        print("⚠️  Running in DEBUG mode - auto-creating tables")
        Base.metadata.create_all(bind=engine)
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"📚 API Documentation: http://localhost:8000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print(f"👋 {settings.APP_NAME} shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

