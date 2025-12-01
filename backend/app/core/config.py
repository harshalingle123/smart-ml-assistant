from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path


class Settings(BaseSettings):
    MONGO_URI: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    ENVIRONMENT: str = "development"

    # File Upload Configuration (environment-dependent)
    # Set conservative defaults, will be overridden based on environment
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # Default: 20 MB
    MAX_UPLOAD_SIZE_MB: int = 20  # For display purposes

    # Dataset Processing Limits (memory-efficient)
    MAX_DATASET_ROWS_IN_MEMORY: int = 1000  # Max rows to load at once
    MAX_SAMPLE_ROWS: int = 100  # Max sample rows for display

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override limits based on environment
        if self.ENVIRONMENT == "production":
            # Production: Strict limits for 512MB RAM instances (Render free tier)
            self.MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB
            self.MAX_UPLOAD_SIZE_MB = 20
        else:
            # Development: More generous limits
            self.MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
            self.MAX_UPLOAD_SIZE_MB = 100

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None

    # Claude AI Configuration (Alternative)
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4096

    # Google Gemini Configuration (Primary AI)
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"  # Fast and free model

    # Kaggle API Configuration
    KAGGLE_USERNAME: Optional[str] = None
    KAGGLE_KEY: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        # Get the backend directory path (two levels up from this file)
        backend_dir = Path(__file__).parent.parent.parent
        env_file = str(backend_dir / ".env")
        case_sensitive = True


settings = Settings()
