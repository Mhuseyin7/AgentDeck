import pytest

from app.models import TaskStatus
from app.states import validate_transition


def test_valid_lifecycle_transition() -> None:
    validate_transition(TaskStatus.PENDING, TaskStatus.PREPARING)
    validate_transition(TaskStatus.RUNNING, TaskStatus.TESTING)
    validate_transition(TaskStatus.TESTING, TaskStatus.SUCCEEDED)


def test_terminal_tasks_cannot_transition() -> None:
    with pytest.raises(ValueError):
        validate_transition(TaskStatus.SUCCEEDED, TaskStatus.RUNNING)
