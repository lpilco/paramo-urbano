"""Redis-backed queue producer and consumer for asynchronous telemetry tasks."""

import asyncio
from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import redis.asyncio as aioredis

from backend.src.application.interfaces.queue_interface import (
    JobQueueConsumer,
    JobQueueProducer,
)

load_dotenv()


class RedisJobQueue(JobQueueProducer, JobQueueConsumer):
    """Asynchronous job queue client supporting Redis list semantics with in-memory fallback."""

    QUEUE_KEY: str = "paramo:queue:telemetry_ingestion"

    def __init__(
        self,
        redis_url: Optional[str] = None,
        queue_key: Optional[str] = None,
        use_in_memory: bool = False,
    ) -> None:
        """Initialize the Redis job queue client.

        Args:
            redis_url (Optional[str], optional): Redis connection URI.
            queue_key (Optional[str], optional): Target queue key. Defaults to standard key.
            use_in_memory (bool, optional): Force in-memory queue for testing.
        """
        raw_url = redis_url or os.getenv("REDIS_URL")
        if not raw_url:
            host = os.getenv("REDIS_HOST", "localhost")
            port = os.getenv("REDIS_PORT", "6379")
            password = os.getenv("REDIS_PASSWORD", "")
            auth = f":{password}@" if password else ""
            raw_url = f"redis://{auth}{host}:{port}/0"

        self.redis_url = raw_url
        self.queue_key = queue_key or self.QUEUE_KEY
        self.use_in_memory = use_in_memory
        self._memory_queue: asyncio.Queue[str] = asyncio.Queue()
        self._client: Optional[aioredis.Redis] = None

    async def _get_client(self) -> Optional[aioredis.Redis]:
        """Obtain or initialize the active async Redis client."""
        if self.use_in_memory:
            return None

        if self._client is None:
            try:
                client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                )
                await client.ping()
                self._client = client
            except Exception:
                # Silently fall back to in-memory queue if Redis is not running
                self.use_in_memory = True
                self._client = None

        return self._client

    async def enqueue_telemetry_job(
        self,
        job_id: str,
        athlete_profile_id: str,
        file_storage_key: str,
        file_hash_sha256: str,
    ) -> None:
        """Enqueue an activity telemetry processing task."""
        payload: Dict[str, Any] = {
            "job_id": job_id,
            "athlete_profile_id": athlete_profile_id,
            "file_storage_key": file_storage_key,
            "file_hash_sha256": file_hash_sha256.lower(),
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
            "retry_count": 0,
        }
        serialized = json.dumps(payload)
        client = await self._get_client()

        if client is not None:
            try:
                await client.lpush(self.queue_key, serialized)
                return
            except Exception:
                self.use_in_memory = True

        await self._memory_queue.put(serialized)

    async def dequeue_telemetry_job(self, timeout_seconds: int = 1) -> Optional[Dict[str, Any]]:
        """Dequeue the next processing job from the queue."""
        client = await self._get_client()

        if client is not None:
            try:
                result = await client.brpop(self.queue_key, timeout=timeout_seconds)
                if result is not None:
                    _, raw_payload = result
                    return json.loads(raw_payload)
                return None
            except Exception:
                self.use_in_memory = True

        try:
            raw_payload = await asyncio.wait_for(self._memory_queue.get(), timeout=float(timeout_seconds))
            return json.loads(raw_payload)
        except (asyncio.TimeoutError, TimeoutError):
            return None

    async def queue_size(self) -> int:
        """Return the current number of pending items in the queue."""
        client = await self._get_client()
        if client is not None:
            try:
                return await client.llen(self.queue_key)
            except Exception:
                self.use_in_memory = True

        return self._memory_queue.qsize()

    async def close(self) -> None:
        """Close Redis connection resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
