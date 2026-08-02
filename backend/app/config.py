from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "GymAI Tracker"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite+aiosqlite:///./gymai.db"
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
