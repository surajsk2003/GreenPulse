from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database - AWS RDS PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/greenpulse")
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "GreenPulse"
    VERSION: str = "1.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS - AWS CloudFront and S3
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:4200", 
        "http://localhost:3000",
        "https://*.amazonaws.com",
        "https://*.cloudfront.net"
    ]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ML Models
    MODEL_STORAGE_PATH: str = "./models"
    MLFLOW_TRACKING_URI: str = "sqlite:///mlflow.db"
    
    # Data Processing
    BATCH_SIZE: int = 10000
    MAX_WORKERS: int = 4
    
    class Config:
        env_file = ".env"

settings = Settings()