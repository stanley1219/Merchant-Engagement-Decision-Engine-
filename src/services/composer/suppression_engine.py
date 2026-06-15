import hashlib
import json

from src.core.config import get_settings
from src.core.constants import SUPPRESSION_PREFIX
from src.infrastructure.cache.redis_client import RedisClient

settings = get_settings()


def _build_suppression_key(
    merchant_id: str,
    trigger_type: str,
    signal_data: dict,
    customer_id: str | None = None,
) -> str:
    deterministic = json.dumps(signal_data, sort_keys=True)
    signal_hash = hashlib.sha256(deterministic.encode()).hexdigest()[:12]
    parts = [trigger_type, merchant_id, signal_hash]
    if customer_id:
        parts.append(customer_id)
    return f"{SUPPRESSION_PREFIX}{'_'.join(parts)}"


class SuppressionEngine:
    def __init__(self, redis: RedisClient) -> None:
        self._redis = redis

    async def is_suppressed(
        self,
        merchant_id: str,
        trigger_type: str,
        signal_data: dict,
        customer_id: str | None = None,
    ) -> bool:
        key = _build_suppression_key(
            merchant_id=merchant_id,
            trigger_type=trigger_type,
            signal_data=signal_data,
            customer_id=customer_id,
        )
        return await self._redis.exists(key)

    async def suppress(
        self,
        merchant_id: str,
        trigger_type: str,
        signal_data: dict,
        customer_id: str | None = None,
        ttl: int | None = None,
    ) -> str:
        key = _build_suppression_key(
            merchant_id=merchant_id,
            trigger_type=trigger_type,
            signal_data=signal_data,
            customer_id=customer_id,
        )
        await self._redis.set(
            key,
            "1",
            ttl=ttl or settings.DEFAULT_SUPPRESSION_TTL,
        )
        return key

    async def check_and_suppress(
        self,
        merchant_id: str,
        trigger_type: str,
        signal_data: dict,
        customer_id: str | None = None,
        ttl: int | None = None,
    ) -> tuple[bool, str]:
        key = _build_suppression_key(
            merchant_id=merchant_id,
            trigger_type=trigger_type,
            signal_data=signal_data,
            customer_id=customer_id,
        )
        ttl = ttl or settings.DEFAULT_SUPPRESSION_TTL
        set_ok = await self._redis.client.set(key, "1", ex=ttl, nx=True)
        if set_ok:
            return False, key
        return True, key

    async def clear(
        self,
        merchant_id: str,
        trigger_type: str,
        signal_data: dict,
        customer_id: str | None = None,
    ) -> None:
        key = _build_suppression_key(
            merchant_id=merchant_id,
            trigger_type=trigger_type,
            signal_data=signal_data,
            customer_id=customer_id,
        )
        await self._redis.delete(key)

    async def get_ttl(
        self,
        merchant_id: str,
        trigger_type: str,
        signal_data: dict,
        customer_id: str | None = None,
    ) -> int:
        key = _build_suppression_key(
            merchant_id=merchant_id,
            trigger_type=trigger_type,
            signal_data=signal_data,
            customer_id=customer_id,
        )
        return await self._redis.ttl(key)
