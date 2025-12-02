# app/settings.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "super-clave-ultra-secreta-123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
