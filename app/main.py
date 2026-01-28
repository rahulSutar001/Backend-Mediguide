"""
MediGuide FastAPI Application
Production-grade backend for medical report analysis
"""

import logging
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.routes import reports, chat, family, premium, chatbot, admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="MediGuide AI - Medical Report Analysis API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - use settings to allow environment configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(family.router, prefix=settings.API_V1_PREFIX)
app.include_router(premium.router, prefix=settings.API_V1_PREFIX)
app.include_router(chatbot.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)

from pydantic import BaseModel


class TokenCheck(BaseModel):
    token: str


@app.post("/api/v1/debug/token")
async def debug_token_check(body: TokenCheck):
    """Temporary debug endpoint to test token verification logic"""
    try:
        from app.core.security import verify_jwt_token

        user = await verify_jwt_token(body.token)
        return {
            "status": "valid",
            "user": user,
            "supabase_url": settings.SUPABASE_URL,
        }
    except Exception as e:
        return {
            "status": "invalid",
            "error": str(e),
            "supabase_url": settings.SUPABASE_URL,
        }


@app.post("/api/v1/debug/ocr")
async def debug_ocr(file: UploadFile = File(...)):
    """Diagnostic endpoint to test Tesseract directly on the server."""
    import pytesseract
    import shutil
    import os
    from PIL import Image
    import io
    import sys

    response_data = {
        "status": "pending",
        "env_path": os.environ.get("PATH", ""),
        "python_executable": sys.executable,
        "cwd": os.getcwd(),
        "tesseract_locations_checked": {},
        "shutil_which_tesseract": str(shutil.which("tesseract")),
    }

    try:
        # 1. Log Request
        logger.info(f"Debug OCR request received for file: {file.filename}")

        # 2. Check manually in common paths
        common_paths = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/nix/var/nix/profiles/default/bin/tesseract",
            "/bin/tesseract",
        ]

        found_binary = None
        for p in common_paths:
            exists = os.path.exists(p)
            response_data["tesseract_locations_checked"][p] = exists
            if exists:
                found_binary = p

        # 3. Try to configure pytesseract if we found it
        if found_binary and not shutil.which("tesseract"):
            pytesseract.pytesseract.tesseract_cmd = found_binary
            response_data["manual_path_configured"] = found_binary

        # 4. Check Tesseract Version/Path (After potential fix)
        try:
            version = pytesseract.get_tesseract_version()
            cli_path = pytesseract.pytesseract.tesseract_cmd
        except Exception as e:
            version = f"Error: {e}"
            cli_path = "Unknown"

        response_data["tesseract_version"] = str(version)
        response_data["tesseract_cmd_final"] = str(cli_path)

        # 5. Read Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        response_data["image_size"] = image.size

        # 6. Run OCR
        text = pytesseract.image_to_string(image)

        response_data["status"] = "success"
        response_data["extracted_text_preview"] = (
            text[:500] if text else "No text extracted"
        )
        response_data["full_text_length"] = len(text)

        return response_data

    except Exception as e:
        import traceback

        response_data["status"] = "failed"
        response_data["error"] = str(e)
        response_data["traceback"] = traceback.format_exc()
        return response_data


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MediGuide API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with proper logging"""
    import traceback

    # Log the full error traceback
    error_traceback = traceback.format_exc()
    logger.error(f"Unhandled exception: {str(exc)}\n{error_traceback}")
    print(f"[ERROR] Unhandled exception: {str(exc)}")
    print(f"[ERROR] Traceback:\n{error_traceback}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc)
            if settings.DEBUG
            else "An unexpected error occurred",
            "code": "INTERNAL_SERVER_ERROR",
            "details": error_traceback if settings.DEBUG else None,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG
    )
