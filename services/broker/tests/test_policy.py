from uuid import uuid4

import pytest

from app.policy import RunRequest


def payload() -> dict[str, str]:
    return {
        "task_id": str(uuid4()),
        "adapter": "fake",
        "repository_url": "https://example.test/repo.git",
        "branch": "agent/test",
        "prompt": "change fixture",
    }


def test_fake_defaults_to_network_off() -> None:
    assert RunRequest.model_validate(payload()).network == "OFF"


def test_rejects_network_and_local_clone() -> None:
    with pytest.raises(ValueError):
        RunRequest.model_validate({**payload(), "network": "FULL"})
    with pytest.raises(ValueError):
        RunRequest.model_validate({**payload(), "repository_url": "file:///etc/passwd"})
