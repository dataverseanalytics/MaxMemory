from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Max_Memory"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@maxmemory.com"
    EMAIL_FROM_NAME: str = "Max Memory"
    
    # Frontend
    FRONTEND_URL: str
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Memory System
    OPENAI_API_KEY: str
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    AURA_INSTANCEID: str = ""
    AURA_INSTANCENAME: str = ""
    UPLOAD_DIR: str = "uploads"
    
    # Model Configuration
    DEFAULT_MODEL: str = "gpt-4o-mini"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
        "protected_namespaces": ("model_", ) 
    }


# Global settings instance
settings = Settings()
