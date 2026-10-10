import pytest
from cryptography.fernet import Fernet

from app.config import Settings


def test_production_rejects_development_credentials() -> None:
    settings = Settings(environment="production")
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        settings.validate_runtime()


def test_production_rejects_wildcard_cors() -> None:
    settings = Settings(
        environment="production",
        session_secret="x" * 40,
        broker_shared_token="y" * 40,
        fernet_master_key=Fernet.generate_key().decode(),
        cors_origins="*",
    )
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        settings.validate_runtime()
