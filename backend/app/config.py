from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    secret_key: str = "your-secret-key-here-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite:///./app.db"
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
