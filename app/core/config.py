"""
Application configuration and environment variables
"""
from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import Optional, Any


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = ""
    SUPABASE_ANON_KEY: Optional[str] = ""
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None  # Only for storage operations
    
    @model_validator(mode='after')
    def clean_supabase_config(self):
        if self.SUPABASE_URL and not self.SUPABASE_URL.endswith('/'):
            self.SUPABASE_URL += '/'
        if self.SUPABASE_ANON_KEY:
            self.SUPABASE_ANON_KEY = self.SUPABASE_ANON_KEY.strip()
        if self.SUPABASE_SERVICE_ROLE_KEY:
            self.SUPABASE_SERVICE_ROLE_KEY = self.SUPABASE_SERVICE_ROLE_KEY.strip()
        return self
    
    # OpenAI Configuration (removed - migrated to Gemini)
    # OPENAI_API_KEY: Optional[str] = None
    # OPENAI_MODEL: str = "gpt-4o-mini"

    
    # OCR Configuration
    OCR_SERVICE: str = "tesseract"  # Options: tesseract, google_vision, aws_textract
    GOOGLE_VISION_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Application Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MediGuide API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = []

    @model_validator(mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: dict[str, Any]) -> dict[str, Any]:
        if isinstance(v.get("BACKEND_CORS_ORIGINS"), str) and not v.get("BACKEND_CORS_ORIGINS", "").startswith("["):
            v["BACKEND_CORS_ORIGINS"] = [i.strip() for i in v["BACKEND_CORS_ORIGINS"].split(",")]
        elif isinstance(v.get("BACKEND_CORS_ORIGINS"), (list, str)):
             # Let Pydantic handle lists or JSON strings
             pass
        return v
    
    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Combine defaults with env vars"""
        defaults = [
            "http://localhost:8080",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
        return defaults + self.BACKEND_CORS_ORIGINS

    # File Upload Settings
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    
    # Supabase Storage
    STORAGE_BUCKET: str = "medical-reports"
    
    # Background Processing
    USE_CELERY: bool = False  # Set to True for production with Redis
    CELERY_BROKER_URL: Optional[str] = None
    
    # Rate Limiting
    FREE_TIER_REPORTS_PER_MONTH: int = 3
    FREE_TIER_FAMILY_MEMBERS: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
