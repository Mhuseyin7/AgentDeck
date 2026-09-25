from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://agentdeck:agentdeck@localhost:5432/agentdeck"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: str = "development-only-replace-me-with-32-characters"
    cors_origins: str = "http://localhost:3000"
    broker_url: str = "http://execution-broker:8081"
    broker_shared_token: str = "development-broker-token"


settings = Settings()
