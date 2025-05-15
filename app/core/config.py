
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'sqlite+aiosqlite:///./sql_app.db')
    API_V1_STR: str = "/api/v1"

settings = Settings()
