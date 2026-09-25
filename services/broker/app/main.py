import hmac
import json
import os
from pathlib import Path

import docker
from docker.errors import APIError, DockerException
from fastapi import Depends, FastAPI, Header, HTTPException, status

from .policy import BrokerPolicy, NetworkMode, RunRequest, RunResponse

app = FastAPI(title="AgentDeck execution broker", docs_url=None, redoc_url=None)
WORKSPACE_ROOT = Path(os.getenv("BROKER_WORKSPACE_ROOT", "/var/lib/agentdeck/workspaces"))
SHARED_TOKEN = os.getenv("BROKER_SHARED_TOKEN", "")
ALLOW_FULL_NETWORK = os.getenv("BROKER_ALLOW_FULL_NETWORK", "false").lower() == "true"


def verify_broker_token(x_agentdeck_broker_token: str = Header(default="")) -> None:
    if not SHARED_TOKEN or not hmac.compare_digest(x_agentdeck_broker_token, SHARED_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="broker authentication failed"
        )


def docker_client() -> docker.DockerClient:
    try:
        return docker.from_env()
    except DockerException as exc:
        raise HTTPException(status_code=503, detail="docker unavailable") from exc


@app.get("/health")
def health(_: None = Depends(verify_broker_token)) -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/runs", response_model=RunResponse, status_code=201)
def start_run(request: RunRequest, _: None = Depends(verify_broker_token)) -> RunResponse:
    if request.network == NetworkMode.FULL and not ALLOW_FULL_NETWORK:
        raise HTTPException(
            status_code=403, detail="FULL network mode requires explicit broker opt-in"
        )
    workspace = BrokerPolicy.workspace(request.task_id, WORKSPACE_ROOT)
    workspace.mkdir(mode=0o700, parents=True, exist_ok=False)
    client = docker_client()
    try:
        container = client.containers.run(
            image=BrokerPolicy.images[request.adapter],
            name=f"agentdeck-{request.task_id}",
            command=["/usr/local/bin/fake-agent"],  # Never take command text from request.
            detach=True,
            user="10001:10001",
            network_mode="none",
            read_only=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            pids_limit=request.limits.pids_limit,
            mem_limit=f"{request.limits.memory_mb}m",
            nano_cpus=int(request.limits.cpu_count * 1_000_000_000),
            tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"},
            volumes={str(workspace): {"bind": "/workspace", "mode": "rw"}},
            environment={"AGENTDECK_TASK_ID": str(request.task_id)},
            labels={"agentdeck.managed": "true", "agentdeck.task_id": str(request.task_id)},
            remove=False,
        )
    except APIError as exc:
        workspace.rmdir()
        raise HTTPException(status_code=502, detail="sandbox provisioning failed") from exc
    return RunResponse(container_id=container.id, task_id=request.task_id)


@app.delete("/v1/runs/{task_id}", status_code=204)
def cancel_run(task_id: str, _: None = Depends(verify_broker_token)) -> None:
    client = docker_client()
    try:
        container = client.containers.get(f"agentdeck-{task_id}")
        if (
            container.labels.get("agentdeck.managed") != "true"
            or container.labels.get("agentdeck.task_id") != task_id
        ):
            raise HTTPException(status_code=404, detail="managed sandbox not found")
        container.kill()
        container.remove(v=True, force=True)
    except docker.errors.NotFound as exc:
        raise HTTPException(status_code=404, detail="managed sandbox not found") from exc


@app.get("/v1/runs/{task_id}/logs")
def run_logs(task_id: str, _: None = Depends(verify_broker_token)) -> list[dict[str, object]]:
    """Return JSON-lines only; malformed output is represented safely as stdout."""
    client = docker_client()
    try:
        container = client.containers.get(f"agentdeck-{task_id}")
        if (
            container.labels.get("agentdeck.managed") != "true"
            or container.labels.get("agentdeck.task_id") != task_id
        ):
            raise HTTPException(status_code=404, detail="managed sandbox not found")
        lines = (
            container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace").splitlines()
        )
    except docker.errors.NotFound as exc:
        raise HTTPException(status_code=404, detail="managed sandbox not found") from exc
    events: list[dict[str, object]] = []
    for line in lines:
        try:
            decoded = json.loads(line)
            if not isinstance(decoded.get("type"), str) or not isinstance(
                decoded.get("payload"), dict
            ):
                raise TypeError("event must include string type and object payload")
            events.append({"type": decoded["type"], "payload": decoded["payload"]})
        except (ValueError, TypeError, json.JSONDecodeError):
            events.append({"type": "stdout", "payload": {"text": line}})
    return events
