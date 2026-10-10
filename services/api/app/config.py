from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://agentdeck:agentdeck@localhost:5432/agentdeck"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: str = "development-only-replace-me-with-32-characters"
    fernet_master_key: str = "replace-with-a-url-safe-32-byte-fernet-key"
    cors_origins: str = "http://localhost:3000"
    broker_url: str = "http://execution-broker:8081"
    broker_shared_token: str = "development-broker-token"

    def validate_runtime(self) -> None:
        if self.environment.lower() == "production":
            if self.session_secret.startswith("development-") or len(self.session_secret) < 32:
                raise RuntimeError(
                    "SESSION_SECRET must be a unique 32+ character production secret"
                )
            if (
                self.broker_shared_token.startswith("development-")
                or len(self.broker_shared_token) < 32
            ):
                raise RuntimeError(
                    "BROKER_SHARED_TOKEN must be a unique 32+ character production secret"
                )
            if self.fernet_master_key.startswith("replace-with-"):
                raise RuntimeError("FERNET_MASTER_KEY must be configured in production")
            try:
                Fernet(self.fernet_master_key.encode("utf-8"))
            except ValueError as exc:
                raise RuntimeError("FERNET_MASTER_KEY must be a valid Fernet key") from exc
            if "*" in self.cors_origins:
                raise RuntimeError("CORS_ORIGINS cannot use wildcard origins with credentials")


settings = Settings()
