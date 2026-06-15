from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text

from src.api.v1.schemas.metadata import HealthResponse
from src.core.config import get_settings
from src.infrastructure.cache.redis_client import RedisClient, get_redis
from src.infrastructure.database.session import get_session

settings = get_settings()
router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
async def health_check(redis: RedisClient = Depends(get_redis)) -> HealthResponse:  # noqa: B008
    db_status = "ok"
    redis_status = "ok"

    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    try:
        await redis.client.ping()
    except Exception:
        redis_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "ok" and redis_status == "ok" else "degraded",
        version=settings.ENVIRONMENT,
        timestamp=datetime.now(UTC).isoformat(),
        dependencies={
            "database": db_status,
            "redis": redis_status,
        },
    )
