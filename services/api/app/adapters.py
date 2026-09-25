from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdapterEvent:
    type: str
    payload: dict[str, Any]


class AgentAdapter(ABC):
    """Provider-neutral contract. Concrete adapters never run on the control-plane host."""

    @abstractmethod
    def validate_configuration(self) -> None: ...
    @abstractmethod
    def prepare(self) -> None: ...
    @abstractmethod
    def start(self) -> None: ...
    @abstractmethod
    def stream_events(self) -> Iterator[AdapterEvent]: ...
    @abstractmethod
    def cancel(self) -> None: ...
    @abstractmethod
    def get_usage(self) -> dict[str, Any]: ...
    @abstractmethod
    def cleanup(self) -> None: ...


class FakeAgentAdapter(AgentAdapter):
    """CI-only deterministic event contract; production execution uses the broker image."""

    def validate_configuration(self) -> None:
        pass

    def prepare(self) -> None:
        pass

    def start(self) -> None:
        pass

    def stream_events(self) -> Iterator[AdapterEvent]:
        yield AdapterEvent("agent_started", {"adapter": "fake"})
        yield AdapterEvent("file_modified", {"path": "src/fixture.ts"})
        yield AdapterEvent("test_finished", {"success": True})
        yield AdapterEvent("task_completed", {"exit_code": 0})

    def cancel(self) -> None:
        pass

    def get_usage(self) -> dict[str, Any]:
        return {}

    def cleanup(self) -> None:
        pass
