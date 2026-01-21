"""
환경 변수 및 전역 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 전역 설정"""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/keyworld"
    
    # API Keys
    APIFY_TOKEN: str
    YOUTUBE_API_KEY: str
    OPENAI_API_KEY: str
    
    # Google Sheets (Optional - 호환성 유지)
    GOOGLE_SHEET_ID: Optional[str] = None
    
    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
