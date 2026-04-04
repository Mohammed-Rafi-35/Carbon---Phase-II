from __future__ import annotations

import pickle
import threading
from time import time
from typing import Any

from app.core.config import get_settings


try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class TTLCacheService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._redis = self._build_redis_client()

    def _build_redis_client(self):
        if redis is None or not self.settings.redis_url or self.settings.app_env == "test":
            return None

        try:
            client = redis.Redis.from_url(self.settings.redis_url, decode_responses=False)
            client.ping()
            return client
        except Exception:
            return None

    def get(self, key: str) -> Any | None:
        if self._redis is not None:
            try:
                payload = self._redis.get(key)
                if payload is None:
                    return None
                return pickle.loads(payload)
            except Exception:
                return None

        with self._lock:
            row = self._store.get(key)
            if row is None:
                return None

            expires_at, value = row
            if expires_at <= time():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if self._redis is not None:
            try:
                self._redis.setex(key, max(1, ttl_seconds), pickle.dumps(value))
                return
            except Exception:
                pass

        with self._lock:
            self._store[key] = (time() + max(1, ttl_seconds), value)

    def clear(self) -> None:
        if self._redis is not None:
            try:
                self._redis.flushdb()
                return
            except Exception:
                pass

        with self._lock:
            self._store.clear()


analytics_cache = TTLCacheService()
