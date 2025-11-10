import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development-12345")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database settings
    DB_USER: str = os.getenv("DB_USER", "devuser")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "devpass")
    DB_HOST: str = os.getenv("DB_HOST", "db")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "nra")
    
    class Config:
        env_file = ".env"

settings = Settings()