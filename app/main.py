from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.v1.router import api_router
from app.database import engine, Base
import logging
import time
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create database tables
logger.info("🗄️  Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("✅ Database tables created")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Max Memory - Authentication API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Global exception handler - logs all errors to terminal
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ UNHANDLED EXCEPTION on {request.method} {request.url.path}")
    logger.error(f"❌ Error Type: {type(exc).__name__}")
    logger.error(f"❌ Error Message: {str(exc)}")
    logger.error(f"❌ Full Traceback:")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "type": type(exc).__name__
        }
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"🌐 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"✅ {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}s")
    
    return response


# Include API routes
app.include_router(api_router, prefix=f"/api/{settings.API_VERSION}")


@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("🏠 Root endpoint accessed")
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("💚 Health check endpoint accessed")
    return {"status": "healthy"}
