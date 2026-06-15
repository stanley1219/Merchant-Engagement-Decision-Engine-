from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.schemas.context import ContextRequest, ContextResponse
from src.core.constants import Scope
from src.core.logging import get_logger
from src.infrastructure.cache.redis_client import RedisClient, get_redis
from src.services.context_store.merchant_repo import MerchantRepository

logger = get_logger(__name__)
router = APIRouter()
merchant_repo = MerchantRepository()


@router.post("/context", response_model=ContextResponse)
async def upsert_context(
    body: ContextRequest,
    redis: RedisClient = Depends(get_redis),
) -> ContextResponse:
    ack_id = str(uuid4())
    payload = body.payload

    if body.scope == Scope.MERCHANT.value:
        merchant_id = body.context_id
        normalized = dict(payload)
        if "category_slug" in normalized and "category" not in normalized:
            normalized["category"] = normalized["category_slug"]
        if "offers" in normalized:
            for offer in normalized["offers"]:
                if "name" not in offer and "title" in offer:
                    offer["name"] = offer["title"]
        await redis.set(f"merchant:{merchant_id}", normalized)
        try:
            result = await merchant_repo.upsert(
                scope=body.scope,
                context_id=merchant_id,
                version=body.version,
                payload=payload,
            )
            logger.info("Merchant context upserted", merchant_id=merchant_id, version=body.version, ack_id=ack_id)
        except Exception as e:
            logger.warning("Merchant PG upsert failed (cached in Redis)", merchant_id=merchant_id, error=str(e))

    elif body.scope == Scope.CUSTOMER.value:
        customer_id = body.context_id
        await redis.set(f"customer:{customer_id}", payload)
        logger.info("Customer context cached", context_id=customer_id, version=body.version)

    elif body.scope == "trigger":
        trigger_id = body.context_id
        normalized = dict(payload)
        if "kind" in normalized and "type" not in normalized:
            normalized["type"] = normalized["kind"]
        await redis.set(f"trigger:{trigger_id}", normalized)
        logger.info("Trigger context cached", context_id=trigger_id, version=body.version)

    elif body.scope == "category":
        cat_id = body.context_id
        await redis.set(f"category:{cat_id}", payload)
        logger.info("Category context cached", category_id=cat_id, version=body.version)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown scope: {body.scope}")

    return ContextResponse(
        accepted=True,
        ack_id=ack_id,
        stored_at=datetime.now(UTC),
    )
