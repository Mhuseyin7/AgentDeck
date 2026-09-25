import json
from uuid import UUID

import redis

from .config import settings

QUEUE_NAME = "agentdeck:tasks"


def client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_task(task_id: UUID) -> None:
    client().lpush(QUEUE_NAME, json.dumps({"task_id": str(task_id)}))
