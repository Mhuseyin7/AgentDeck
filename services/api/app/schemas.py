from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from .models import Role, TaskStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)
    organization_name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    repository_url: str = Field(min_length=1, max_length=2048)
    default_branch: str = "main"
    sandbox_profile: str = "restricted"


class ProjectResponse(ProjectCreate):
    id: UUID
    organization_id: UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    agent_type: str = Field(pattern="^(fake|codex|claude_code|opencode)$")
    prompt: str = Field(min_length=1, max_length=100_000)
    branch: str = Field(pattern=r"^[A-Za-z0-9._/-]{1,255}$")


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    agent_type: str
    prompt: str
    branch: str
    status: TaskStatus
    started_at: datetime | None
    finished_at: datetime | None
    exit_code: int | None
    usage_metadata: dict[str, object]
    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    id: UUID
    task_id: UUID
    type: str
    payload: dict[str, object]
    created_at: datetime
    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    user_id: UUID
    role: Role
    model_config = {"from_attributes": True}
