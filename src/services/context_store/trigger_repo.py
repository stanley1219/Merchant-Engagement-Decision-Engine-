from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete, func, select, update

from src.domain.models.trigger import Trigger
from src.infrastructure.database.session import get_session


class TriggerRepository:
    async def get_by_id(self, trigger_id: UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            result = await session.execute(
                select(Trigger).where(Trigger.id == trigger_id)
            )
            trigger = result.scalar_one_or_none()
            if not trigger:
                return None
            return self._to_dict(trigger)

    async def list_pending(
        self,
        merchant_id: UUID,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        async with get_session() as session:
            stmt = (
                select(Trigger)
                .where(
                    Trigger.merchant_id == merchant_id,
                    Trigger.status == "pending",
                    and_(
                        Trigger.expires_at.is_(None),
                        Trigger.expires_at > now,
                    ),
                )
                .order_by(Trigger.priority.desc(), Trigger.created_at.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_dict(t) for t in result.scalars().all()]

    async def list_pending_all(
        self,
        limit: int = 100,
        batch_size: int = 20,
    ) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        async with get_session() as session:
            stmt = (
                select(Trigger)
                .where(
                    Trigger.status == "pending",
                    and_(
                        Trigger.expires_at.is_(None),
                        Trigger.expires_at > now,
                    ),
                )
                .order_by(Trigger.priority.desc(), Trigger.created_at.asc())
                .limit(batch_size)
            )
            result = await session.execute(stmt)
            return [self._to_dict(t) for t in result.scalars().all()]

    async def mark_processing(self, trigger_id: UUID) -> bool:
        async with get_session() as session:
            result = await session.execute(
                update(Trigger)
                .where(
                    Trigger.id == trigger_id,
                    Trigger.status == "pending",
                )
                .values(
                    status="processing",
                    retry_count=Trigger.retry_count + 1,
                )
            )
            await session.commit()
            return result.rowcount > 0

    async def mark_completed(
        self,
        trigger_id: UUID,
        error_message: str | None = None,
    ) -> bool:
        values: dict[str, Any] = {
            "status": "completed" if not error_message else "failed",
            "processed_at": datetime.now(UTC),
        }
        if error_message:
            values["error_message"] = error_message[:500]

        async with get_session() as session:
            result = await session.execute(
                update(Trigger)
                .where(Trigger.id == trigger_id)
                .values(**values)
            )
            await session.commit()
            return result.rowcount > 0

    async def get_pending_count(self, merchant_id: UUID) -> int:
        async with get_session() as session:
            result = await session.execute(
                select(func.count(Trigger.id)).where(
                    Trigger.merchant_id == merchant_id,
                    Trigger.status == "pending",
                )
            )
            return result.scalar() or 0

    async def delete_expired(self) -> int:
        now = datetime.now(UTC)
        async with get_session() as session:
            result = await session.execute(
                delete(Trigger).where(
                    Trigger.expires_at.isnot(None),
                    Trigger.expires_at <= now,
                    Trigger.status == "pending",
                )
            )
            await session.commit()
            return result.rowcount

    def _to_dict(self, trigger: Trigger) -> dict[str, Any]:
        return {
            "id": str(trigger.id),
            "merchant_id": str(trigger.merchant_id),
            "customer_id": str(trigger.customer_id) if trigger.customer_id else None,
            "type": trigger.type,
            "payload": dict(trigger.payload),
            "priority": trigger.priority,
            "source": trigger.source,
            "status": trigger.status,
            "retry_count": trigger.retry_count,
            "expires_at": trigger.expires_at.isoformat() if trigger.expires_at else None,
            "processed_at": trigger.processed_at.isoformat() if trigger.processed_at else None,
            "error_message": trigger.error_message,
            "created_at": trigger.created_at.isoformat() if trigger.created_at else None,
        }
