
from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./sql_app.db')
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-placeholder')
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh tokens
    
    # Cloudinary config
    CLOUDINARY_CLOUD_NAME: str = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY: str = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET: str = os.getenv('CLOUDINARY_API_SECRET', '')

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Convert async database URL to sync for Alembic"""
        if self.DATABASE_URL.startswith('postgresql+asyncpg://'):
            return self.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql+psycopg2://')
        return self.DATABASE_URL

settings = Settings()
