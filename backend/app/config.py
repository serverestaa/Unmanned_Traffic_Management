# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    database_url: str = Field(default="postgresql+asyncpg://utm_user:utm_password@localhost:5432/utm_db")
    secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    class Config:
        env_file = ".env"


settings = Settings()