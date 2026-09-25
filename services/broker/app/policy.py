from enum import StrEnum
from pathlib import Path
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class NetworkMode(StrEnum):
    OFF = "OFF"
    DEPENDENCY_ONLY = "DEPENDENCY_ONLY"
    ALLOWLIST = "ALLOWLIST"
    FULL = "FULL"


class ResourceLimits(BaseModel):
    cpu_count: float = Field(default=1, ge=0.25, le=4)
    memory_mb: int = Field(default=1024, ge=256, le=8192)
    pids_limit: int = Field(default=128, ge=16, le=256)
    timeout_seconds: int = Field(default=900, ge=10, le=3600)
    workspace_mb: int = Field(default=1024, ge=128, le=10240)


class RunRequest(BaseModel):
    task_id: UUID
    adapter: str = Field(pattern=r"^(fake)$")
    network: NetworkMode = NetworkMode.OFF
    limits: ResourceLimits = Field(default_factory=ResourceLimits)
    repository_url: str = Field(max_length=2048)
    branch: str = Field(pattern=r"^[A-Za-z0-9._/-]{1,255}$")
    prompt: str = Field(min_length=1, max_length=100_000)

    @field_validator("repository_url")
    @classmethod
    def block_local_repository_paths(cls, value: str) -> str:
        if value.startswith(("file:", "/", "\\")):
            raise ValueError("local repository paths are prohibited")
        return value

    @model_validator(mode="after")
    def restrict_network_to_fake_mode(self) -> "RunRequest":
        # Fake adapter has no reason for egress. Provider adapters need reviewed policy implementations.
        if self.network != NetworkMode.OFF:
            raise ValueError("network is unavailable for this adapter")
        return self


class RunResponse(BaseModel):
    container_id: str
    task_id: UUID


class BrokerPolicy:
    # Digest pinning is mandatory in a production registry. The local tag exists only for development.
    images: ClassVar[dict[str, str]] = {"fake": "agentdeck/fake-adapter:dev"}

    @staticmethod
    def workspace(task_id: UUID, root: Path) -> Path:
        candidate = (root / str(task_id)).resolve()
        if root.resolve() not in candidate.parents:
            raise ValueError("unsafe workspace path")
        return candidate
