import json
from typing import Any, Optional, List, Union
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.core.config import get_settings
from src.core.exceptions import CacheError

settings = get_settings()


class RedisClient:
    def __init__(self):
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        try:
            self._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                decode_responses=True,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            await self._client.ping()
        except RedisError as e:
            raise CacheError(f"Failed to connect to Redis: {e}")

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()

    @property
    def client(self) -> Redis:
        if not self._client:
            raise CacheError("Redis client not initialized")
        return self._client

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> bool:
        try:
            serialized = json.dumps(value, default=str) if not isinstance(value, str) else value
            return await self._client.set(key, serialized, ex=ttl, nx=nx)
        except RedisError as e:
            raise CacheError(f"Failed to set key {key}: {e}")

    async def get(self, key: str, default: Any = None) -> Any:
        try:
            value = await self._client.get(key)
            if value is None:
                return default
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except RedisError as e:
            raise CacheError(f"Failed to get key {key}: {e}")

    async def delete(self, *keys: str) -> int:
        try:
            return await self._client.delete(*keys)
        except RedisError as e:
            raise CacheError(f"Failed to delete keys {keys}: {e}")

    async def exists(self, key: str) -> bool:
        try:
            return await self._client.exists(key) > 0
        except RedisError as e:
            raise CacheError(f"Failed to check key {key}: {e}")

    async def expire(self, key: str, ttl: int) -> bool:
        try:
            return await self._client.expire(key, ttl)
        except RedisError as e:
            raise CacheError(f"Failed to expire key {key}: {e}")

    async def ttl(self, key: str) -> int:
        try:
            return await self._client.ttl(key)
        except RedisError as e:
            raise CacheError(f"Failed to get TTL for key {key}: {e}")

    async def hset(self, name: str, mapping: dict) -> int:
        try:
            serialized = {k: json.dumps(v, default=str) if not isinstance(v, str) else v for k, v in mapping.items()}
            return await self._client.hset(name, mapping=serialized)
        except RedisError as e:
            raise CacheError(f"Failed to hset {name}: {e}")

    async def hget(self, name: str, key: str) -> Any:
        try:
            value = await self._client.hget(name, key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except RedisError as e:
            raise CacheError(f"Failed to hget {name}:{key}: {e}")

    async def hgetall(self, name: str) -> dict:
        try:
            data = await self._client.hgetall(name)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except json.JSONDecodeError:
                    result[k] = v
            return result
        except RedisError as e:
            raise CacheError(f"Failed to hgetall {name}: {e}")

    async def hdel(self, name: str, *keys: str) -> int:
        try:
            return await self._client.hdel(name, *keys)
        except RedisError as e:
            raise CacheError(f"Failed to hdel {name}: {e}")

    async def sadd(self, name: str, *values: str) -> int:
        try:
            return await self._client.sadd(name, *values)
        except RedisError as e:
            raise CacheError(f"Failed to sadd {name}: {e}")

    async def smembers(self, name: str) -> set:
        try:
            return await self._client.smembers(name)
        except RedisError as e:
            raise CacheError(f"Failed to smembers {name}: {e}")

    async def sismember(self, name: str, value: str) -> bool:
        try:
            return await self._client.sismember(name, value)
        except RedisError as e:
            raise CacheError(f"Failed to sismember {name}: {e}")

    async def incr(self, key: str) -> int:
        try:
            return await self._client.incr(key)
        except RedisError as e:
            raise CacheError(f"Failed to incr {key}: {e}")

    async def keys(self, pattern: str) -> List[str]:
        try:
            return await self._client.keys(pattern)
        except RedisError as e:
            raise CacheError(f"Failed to keys {pattern}: {e}")

    @asynccontextmanager
    async def pipeline(self):
        try:
            pipe = self._client.pipeline()
            yield pipe
            await pipe.execute()
        except RedisError as e:
            raise CacheError(f"Pipeline execution failed: {e}")


redis_client = RedisClient()


async def get_redis() -> RedisClient:
    return redis_client