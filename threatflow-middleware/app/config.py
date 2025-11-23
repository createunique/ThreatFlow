"""
Configuration management using Pydantic Settings
Loads environment variables from .env file
"""

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # IntelOwl Configuration
    INTELOWL_URL: str = "http://localhost"
    INTELOWL_API_KEY: str
    
    # API Configuration
    API_TITLE: str = "ThreatFlow Middleware"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001", 
        "http://localhost:3002",
        "http://127.0.0.1:3002"
    ]
    
    # Timeouts (seconds)
    ANALYSIS_TIMEOUT: int = 300
    POLL_INTERVAL: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()