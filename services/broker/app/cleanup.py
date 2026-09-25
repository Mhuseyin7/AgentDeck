"""Safe orphan reconciliation, intended to run as a scheduled broker-only job."""

from datetime import UTC, datetime, timedelta

import docker


def cleanup_expired(max_age_hours: int = 24) -> int:
    client = docker.from_env()
    cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
    removed = 0
    for container in client.containers.list(all=True, filters={"label": "agentdeck.managed=true"}):
        created = datetime.fromisoformat(container.attrs["Created"])
        if created < cutoff:
            container.remove(v=True, force=True)
            removed += 1
    return removed
