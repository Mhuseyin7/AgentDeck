import pytest
from pydantic import ValidationError

from app.schemas import TaskCreate


def test_unsupported_provider_is_rejected_until_configured() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(agent_type="codex", prompt="run tests", branch="agent/tests")
