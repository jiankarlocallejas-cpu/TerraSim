"""
Configuration settings for the TerraSim application.
"""

from pydantic import AnyHttpUrl, validator, root_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any, Union
import secrets
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "TerraSim"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    SERVER_NAME: str = "terrasim"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "terrasim")
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "true").lower() == "true"
    DATABASE_URI: Optional[str] = None

    @root_validator(pre=False, skip_on_failure=True)
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Set DATABASE_URI based on USE_SQLITE setting
        if values.get('USE_SQLITE'):
            values['DATABASE_URI'] = "sqlite:///./terrasim.db"
        else:
            pg_user = values.get('POSTGRES_USER', 'postgres')
            pg_pass = values.get('POSTGRES_PASSWORD', '')
            pg_server = values.get('POSTGRES_SERVER', 'localhost')
            pg_db = values.get('POSTGRES_DB', 'terrasim')
            values['DATABASE_URI'] = f"postgresql://{pg_user}:{pg_pass}@{pg_server}/{pg_db}"
        return values

    # Storage settings
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # 'local' or 's3'
    LOCAL_STORAGE_PATH: str = os.getenv("LOCAL_STORAGE_PATH", "./data")
    S3_ENDPOINT: Optional[str] = os.getenv("S3_ENDPOINT")
    S3_ACCESS_KEY: Optional[str] = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = os.getenv("S3_SECRET_KEY")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "terrasim-data")

    # PDAL settings
    PDAL_PATH: str = os.getenv("PDAL_PATH", "pdal")
    
    # GDAL settings
    GDAL_CACHE_MAX: int = int(os.getenv("GDAL_CACHE_MAX", "512"))
    
    # Worker settings
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    
    # Security
    SECURITY_PASSWORD_SALT: str = os.getenv("SECURITY_PASSWORD_SALT", secrets.token_urlsafe(32))
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # First superuser
    FIRST_SUPERUSER: str = os.getenv("FIRST_SUPERUSER", "admin@terrasim.org")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "TerraSim2025")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables

# Create settings instance
settings = Settings()
