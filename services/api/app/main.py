from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import create_access_token, current_user, organization_role
from .config import settings
from .db import Base, engine, get_db
from .models import (
    AuditLog,
    Organization,
    OrganizationMember,
    Project,
    Role,
    Task,
    TaskEvent,
    TaskStatus,
    User,
)
from .queue import enqueue_task
from .schemas import (
    LoginRequest,
    ProjectCreate,
    ProjectResponse,
    RegisterRequest,
    TaskCreate,
    TaskResponse,
    TokenResponse,
)
from .security import hash_password, verify_password
from .states import validate_transition


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)  # Replace with Alembic migrations in production rollout.
    yield


app = FastAPI(
    title="AgentDeck API", version="0.1.0", openapi_url="/api/v1/openapi.json", lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
API = "/api/v1"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ready"}


@app.post(f"{API}/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.scalar(select(User).where(User.email == str(payload.email))):
        raise HTTPException(status_code=409, detail="email already registered")
    user = User(email=str(payload.email), password_hash=hash_password(payload.password))
    organization = Organization(name=payload.organization_name)
    db.add_all([user, organization])
    db.flush()
    db.add(OrganizationMember(organization_id=organization.id, user_id=user.id, role=Role.OWNER))
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id))


@app.post(f"{API}/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email)))
    if user is None or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=401, detail="invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@app.get(f"{API}/organizations")
def organizations(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[dict[str, str]]:
    rows = db.execute(
        select(Organization, OrganizationMember.role)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == user.id)
    ).all()
    return [{"id": str(org.id), "name": org.name, "role": role.value} for org, role in rows]


@app.post(
    f"{API}/organizations/{{organization_id}}/projects",
    response_model=ProjectResponse,
    status_code=201,
)
def create_project(
    organization_id: UUID,
    payload: ProjectCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Project:
    organization_role(db, organization_id, user.id, Role.OWNER, Role.ADMIN, Role.DEVELOPER)
    project = Project(organization_id=organization_id, **payload.model_dump())
    db.add(project)
    db.add(
        AuditLog(
            organization_id=organization_id,
            actor_id=user.id,
            action="project.created",
            target_type="project",
            target_id=str(project.id),
        )
    )
    db.commit()
    db.refresh(project)
    return project


@app.get(f"{API}/organizations/{{organization_id}}/projects", response_model=list[ProjectResponse])
def list_projects(
    organization_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[Project]:
    organization_role(db, organization_id, user.id)
    return list(
        db.scalars(
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.created_at.desc())
        )
    )


@app.post(f"{API}/projects/{{project_id}}/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    project_id: UUID,
    payload: TaskCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Task:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    organization_role(db, project.organization_id, user.id, Role.OWNER, Role.ADMIN, Role.DEVELOPER)
    task = Task(project_id=project_id, created_by=user.id, **payload.model_dump())
    db.add(task)
    db.flush()
    db.add(
        TaskEvent(
            task_id=task.id,
            type="task_created",
            payload={"agent": task.agent_type, "branch": task.branch},
        )
    )
    db.add(
        AuditLog(
            organization_id=project.organization_id,
            actor_id=user.id,
            action="task.created",
            target_type="task",
            target_id=str(task.id),
        )
    )
    db.commit()
    db.refresh(task)
    enqueue_task(task.id)
    return task


@app.get(f"{API}/projects/{{project_id}}/tasks", response_model=list[TaskResponse])
def list_tasks(
    project_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[Task]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    organization_role(db, project.organization_id, user.id)
    return list(
        db.scalars(select(Task).where(Task.project_id == project_id).order_by(Task.id.desc()))
    )


@app.get(f"{API}/tasks/{{task_id}}", response_model=TaskResponse)
def get_task(
    task_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    project = db.get(Project, task.project_id)
    assert project is not None
    organization_role(db, project.organization_id, user.id)
    return task


@app.post(f"{API}/tasks/{{task_id}}/cancel", response_model=TaskResponse)
def cancel_task(
    task_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> Task:
    task = get_task(task_id, user, db)
    try:
        validate_transition(task.status, TaskStatus.CANCELLED)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    task.status = TaskStatus.CANCELLED
    task.finished_at = datetime.now(UTC)
    db.add(TaskEvent(task_id=task.id, type="task_cancelled", payload={}))
    db.commit()
    db.refresh(task)
    return task


@app.get(f"{API}/tasks/{{task_id}}/events")
def task_events(
    task_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    get_task(task_id, user, db)
    events = db.scalars(
        select(TaskEvent).where(TaskEvent.task_id == task_id).order_by(TaskEvent.created_at)
    ).all()
    return [
        {
            "id": str(e.id),
            "type": e.type,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@app.websocket(f"{API}/tasks/{{task_id}}/stream")
async def stream_task_events(websocket: WebSocket, task_id: UUID) -> None:
    # Authentication is intentionally required via a short-lived token query parameter in production websocket client.
    await websocket.close(code=1008, reason="websocket authentication pending")
