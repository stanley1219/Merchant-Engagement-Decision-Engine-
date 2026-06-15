import asyncio
import signal
from datetime import UTC, datetime
from uuid import UUID

from src.core.config import get_settings
from src.core.constants import Category
from src.core.logging import get_logger, setup_logging
from src.infrastructure.cache.redis_client import redis_client
from src.infrastructure.database.session import close_db, init_db
from src.services.composer.decision_engine import DecisionEngine
from src.services.composer.message_generator import MessageGenerator
from src.services.composer.suppression_engine import SuppressionEngine
from src.services.context_store.customer_repo import CustomerRepository
from src.services.context_store.merchant_repo import MerchantRepository
from src.services.context_store.trigger_repo import TriggerRepository

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


class TickProcessor:
    def __init__(self) -> None:
        self._merchant_repo = MerchantRepository()
        self._customer_repo = CustomerRepository()
        self._trigger_repo = TriggerRepository()
        self._suppression = SuppressionEngine(redis_client)
        self._decision_engine = DecisionEngine(self._suppression)
        self._message_gen = MessageGenerator()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        self._running = True
        logger.info(
            "Tick processor started",
            batch_size=settings.TICK_BATCH_SIZE,
            poll_interval=5,
        )

        while self._running:
            try:
                await self._process_batch()
            except Exception as e:
                logger.exception("Batch processing failed", error=str(e))

            await asyncio.sleep(5)

    async def stop(self) -> None:
        self._running = False
        logger.info("Tick processor stopping")

    async def _process_batch(self) -> None:
        triggers = await self._trigger_repo.list_pending_all(
            batch_size=settings.TICK_BATCH_SIZE,
        )

        if not triggers:
            return

        logger.info("Processing trigger batch", count=len(triggers))

        for trigger_data in triggers:
            await self._process_trigger(trigger_data)

    async def _process_trigger(self, trigger_data: dict) -> None:
        trigger_id = UUID(trigger_data["id"])
        merchant_id = UUID(trigger_data["merchant_id"])

        marked = await self._trigger_repo.mark_processing(trigger_id)
        if not marked:
            logger.warning("Trigger already processing", trigger_id=trigger_data["id"])
            return

        try:
            merchant = await self._merchant_repo.get_by_id(merchant_id)
            if not merchant:
                await self._trigger_repo.mark_completed(
                    trigger_id,
                    error_message=f"Merchant not found: {merchant_id}",
                )
                return

            category = merchant.get("category", "")
            customer: dict | None = None
            customer_id_str = trigger_data.get("customer_id")
            if customer_id_str:
                customer = await self._customer_repo.get_by_id(
                    UUID(customer_id_str),
                )

            result = await self._decision_engine.decide(
                category=Category(category),
                merchant=merchant,
                trigger=trigger_data,
                customer=customer,
            )

            if not result:
                await self._trigger_repo.mark_completed(trigger_id)
                logger.info(
                    "No decision for trigger",
                    trigger_id=trigger_data["id"],
                    merchant_id=str(merchant_id),
                )
                return

            output = await self._message_gen.generate(
                decision=result,
                category=category,
                use_llm=False,
            )

            await redis_client.set(
                f"message:{merchant_id}:{trigger_id}",
                {
                    "message": output.message,
                    "cta": output.cta,
                    "send_as": output.send_as,
                    "suppression_key": output.suppression_key,
                    "rationale": output.rationale,
                    "generated_at": datetime.now(UTC).isoformat(),
                },
                ttl=settings.DEFAULT_SUPPRESSION_TTL,
            )

            await self._trigger_repo.mark_completed(trigger_id)

            logger.info(
                "Trigger processed successfully",
                trigger_id=trigger_data["id"],
                merchant_id=str(merchant_id),
                signal=result.signal.signal_type.value,
                score=result.signal.score,
            )

        except Exception as e:
            await self._trigger_repo.mark_completed(
                trigger_id,
                error_message=str(e)[:500],
            )
            logger.exception(
                "Trigger processing failed",
                trigger_id=trigger_data["id"],
                error=str(e),
            )


async def run_worker() -> None:
    loop = asyncio.get_event_loop()
    processor = TickProcessor()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.ensure_future(processor.stop()),
        )

    await init_db()
    logger.info("Database initialized")

    await redis_client.connect()
    logger.info("Redis connected")

    try:
        await processor.start()
    finally:
        await close_db()
        await redis_client.disconnect()
        logger.info("Worker shut down")


if __name__ == "__main__":
    asyncio.run(run_worker())
