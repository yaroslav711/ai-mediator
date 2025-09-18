"""Application settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""
    
    # Telegram Bot
    telegram_bot_token: str
    telegram_bot_username: str  # Без @, например: ai_mediator_bot
    
    # OpenAI
    openai_api_key: str
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/ai_mediator"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
