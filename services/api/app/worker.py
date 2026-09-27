"""Queue consumer. It orchestrates but never imports Docker or executes agent commands."""

import json
import time
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import SessionLocal
from .models import Project, Task, TaskEvent, TaskStatus
from .queue import QUEUE_NAME, client
from .security import redact
from .states import validate_transition

TERMINAL = {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMED_OUT}


def record(db: Session, task: Task, event_type: str, payload: dict[str, object]) -> None:
    safe_payload = {
        key: redact(value) if isinstance(value, str) else value for key, value in payload.items()
    }
    db.add(TaskEvent(task_id=task.id, type=event_type, payload=safe_payload))


def set_status(db: Session, task: Task, status: TaskStatus) -> None:
    validate_transition(task.status, status)
    task.status = status
    if status == TaskStatus.RUNNING:
        task.started_at = datetime.now(UTC)
    if status in {
        TaskStatus.SUCCEEDED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.TIMED_OUT,
    }:
        task.finished_at = datetime.now(UTC)


def execute(task_id: UUID) -> None:
    with SessionLocal() as db:
        task = db.get(Task, task_id)
        if task is None or task.status != TaskStatus.PENDING:
            return
        project = db.get(Project, task.project_id)
        if project is None:
            return
        try:
            set_status(db, task, TaskStatus.PREPARING)
            record(db, task, "agent_preparing", {"adapter": task.agent_type})
            db.commit()
            request = {
                "task_id": str(task.id),
                "adapter": task.agent_type,
                "network": "OFF",
                "repository_url": project.repository_url,
                "branch": task.branch,
                "prompt": task.prompt,
            }
            with httpx.Client(timeout=20) as http:
                result = http.post(
                    f"{settings.broker_url}/v1/runs",
                    json=request,
                    headers={"X-AgentDeck-Broker-Token": settings.broker_shared_token},
                )
                result.raise_for_status()
            set_status(db, task, TaskStatus.RUNNING)
            record(
                db,
                task,
                "agent_started",
                {"container_id": result.json()["container_id"], "adapter": task.agent_type},
            )
            db.commit()
            monitor_run(db, task)
        except (ValueError, httpx.HTTPError) as exc:
            if task.status not in {TaskStatus.FAILED, TaskStatus.CANCELLED}:
                set_status(db, task, TaskStatus.FAILED)
            record(db, task, "task_failed", {"reason": str(exc)})
            db.commit()


def monitor_run(db: Session, task: Task) -> None:
    """Persist broker-produced events and a truthful terminal state; never infer success."""
    headers = {"X-AgentDeck-Broker-Token": settings.broker_shared_token}
    deadline = time.monotonic() + 920
    with httpx.Client(timeout=20) as http:
        while time.monotonic() < deadline:
            db.refresh(task)
            if task.status == TaskStatus.CANCELLED:
                http.delete(f"{settings.broker_url}/v1/runs/{task.id}", headers=headers)
                return
            state = http.get(f"{settings.broker_url}/v1/runs/{task.id}", headers=headers)
            state.raise_for_status()
            details = state.json()
            if not details["running"]:
                events = http.get(f"{settings.broker_url}/v1/runs/{task.id}/logs", headers=headers)
                events.raise_for_status()
                existing = {
                    event.type + str(event.payload)
                    for event in db.scalars(
                        select(TaskEvent).where(TaskEvent.task_id == task.id)
                    ).all()
                }
                for event in events.json():
                    signature = event["type"] + str(event["payload"])
                    if signature not in existing:
                        record(db, task, event["type"], event["payload"])
                exit_code = details.get("exit_code")
                task.exit_code = int(exit_code) if isinstance(exit_code, int) else 1
                if task.exit_code == 0:
                    set_status(db, task, TaskStatus.TESTING)
                    set_status(db, task, TaskStatus.SUCCEEDED)
                else:
                    set_status(db, task, TaskStatus.FAILED)
                    record(
                        db,
                        task,
                        "task_failed",
                        {"reason": details.get("error") or "sandbox exited non-zero"},
                    )
                db.commit()
                return
            time.sleep(0.5)
    if task.status not in TERMINAL:
        set_status(db, task, TaskStatus.TIMED_OUT)
        record(db, task, "task_timed_out", {"timeout_seconds": 920})
        db.commit()


def run_forever() -> None:
    queue = client()
    while True:
        item = queue.brpop(QUEUE_NAME, timeout=5)
        if item is not None:
            execute(UUID(json.loads(item[1])["task_id"]))
        time.sleep(0.05)


if __name__ == "__main__":
    run_forever()
