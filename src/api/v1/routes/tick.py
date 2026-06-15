from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from src.api.v1.schemas.tick import TickRequest, TickResponse
from src.core.constants import Category
from src.core.logging import get_logger
from src.infrastructure.cache.redis_client import RedisClient, get_redis
from src.services.composer.decision_engine import DecisionEngine
from src.services.composer.message_generator import MessageGenerator
from src.services.composer.suppression_engine import SuppressionEngine

logger = get_logger(__name__)
router = APIRouter()


@router.post("/tick", response_model=TickResponse)
async def process_tick(
    body: TickRequest,
    redis: RedisClient = Depends(get_redis),
) -> TickResponse:
    suppression = SuppressionEngine(redis)
    decision_engine = DecisionEngine(suppression)
    message_gen = MessageGenerator()

    actions = []

    for trigger_id in body.available_triggers:
        try:
            trigger = await redis.get(f"trigger:{trigger_id}")
            if not trigger:
                logger.warning("Trigger not found", trigger_id=trigger_id)
                continue

            merchant_id = trigger.get("merchant_id", "")
            if not merchant_id:
                logger.warning("Trigger has no merchant_id", trigger_id=trigger_id)
                continue

            merchant = await redis.get(f"merchant:{merchant_id}")
            if not merchant:
                logger.warning("Merchant not found", merchant_id=merchant_id, trigger_id=trigger_id)
                continue

            category_str = merchant.get("category", "")
            try:
                category = Category(category_str)
            except ValueError:
                logger.warning("Invalid category", category=category_str, merchant_id=merchant_id)
                continue

            customer_id = trigger.get("customer_id")
            customer = None
            if customer_id:
                customer = await redis.get(f"customer:{customer_id}")

            result = await decision_engine.decide(
                category=category,
                merchant=merchant,
                trigger=trigger,
                customer=customer,
                force=True,
            )

            if not result:
                logger.info("No action generated", trigger_id=trigger_id, merchant_id=merchant_id)
                continue

            output = await message_gen.generate(
                decision=result,
                category=category_str,
                use_llm=False,
            )

            actions.append({
                "trigger_id": trigger_id,
                "merchant_id": merchant_id,
                "customer_id": customer_id,
                "body": output.message,
                "cta": output.cta,
                "send_as": output.send_as,
            })

        except Exception as e:
            logger.exception("Tick processing error", trigger_id=trigger_id)

    return TickResponse(actions=actions)
