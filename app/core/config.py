import os
import secrets
from typing import List, Optional, Dict, Any
from pydantic import BaseSettings, AnyHttpUrl, validator

class Settings(BaseSettings):
    """
    Application settings
    
    These settings can be overridden via environment variables
    """
    # Project metadata
    PROJECT_NAME: str = "GLiNER-MLOps"
    API_VERSION: str = "v1"
    
    # App settings
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Model settings
    MODEL_NAME: str = "urchade/gliner_medium-v2.1"
    MODEL_CACHE_DIR: Optional[str] = None
    
    # Security settings
    API_KEY_ENABLED: bool = True
    API_KEY: str = os.getenv("API_KEY", secrets.token_urlsafe(32))
    
    # CORS settings
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"
    
    # Storage settings
    STORAGE_TYPE: str = "local"  # "local", "s3", "gcs", "azure"
    
    # Local storage settings
    LOCAL_STORAGE_PATH: str = "./data"
    
    # AWS S3 settings
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    
    # GCP settings
    GCP_PROJECT_ID: Optional[str] = None
    GCS_BUCKET_NAME: Optional[str] = None
    
    # Azure settings
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER_NAME: Optional[str] = None
    
    # Metrics settings
    METRICS_ENABLED: bool = True
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create instance of settings
settings = Settings()