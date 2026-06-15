from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from src.domain.models.customer import Customer
from src.infrastructure.database.session import get_session


class CustomerRepository:
    async def get_by_id(self, customer_id: UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = result.scalar_one_or_none()
            if not customer:
                return None
            return self._to_dict(customer)

    async def get_by_phone(
        self,
        merchant_id: UUID,
        phone: str,
    ) -> dict[str, Any] | None:
        async with get_session() as session:
            result = await session.execute(
                select(Customer).where(
                    Customer.merchant_id == merchant_id,
                    Customer.phone == phone,
                )
            )
            customer = result.scalar_one_or_none()
            if not customer:
                return None
            return self._to_dict(customer)

    async def get_by_external_id(
        self,
        merchant_id: UUID,
        external_id: str,
    ) -> dict[str, Any] | None:
        async with get_session() as session:
            result = await session.execute(
                select(Customer).where(
                    Customer.merchant_id == merchant_id,
                    Customer.external_id == external_id,
                )
            )
            customer = result.scalar_one_or_none()
            if not customer:
                return None
            return self._to_dict(customer)

    async def list_by_merchant(
        self,
        merchant_id: UUID,
        limit: int = 50,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            stmt = select(Customer).where(Customer.merchant_id == merchant_id)
            if active_only:
                stmt = stmt.where(Customer.is_active.is_(True))
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return [self._to_dict(c) for c in result.scalars().all()]

    async def check_consent(
        self,
        customer_id: UUID,
        channel: str,
    ) -> bool:
        async with get_session() as session:
            result = await session.execute(
                select(Customer.consent_flags).where(Customer.id == customer_id)
            )
            consent_flags = result.scalar_one_or_none()
            if consent_flags is None:
                return False
            return consent_flags.get(channel, False)

    async def update_last_interaction(
        self,
        customer_id: UUID,
    ) -> None:
        async with get_session() as session:
            result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = result.scalar_one_or_none()
            if customer:
                customer.last_interaction_at = datetime.now(UTC)
                await session.commit()

    def _to_dict(self, customer: Customer) -> dict[str, Any]:
        return {
            "identity": {
                "customer_id": str(customer.id),
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "external_id": customer.external_id,
            },
            "profile": dict(customer.profile),
            "consent": dict(customer.consent_flags),
            "tags": list(customer.tags),
            "lifetime_value": customer.lifetime_value,
            "visit_count": customer.visit_count,
            "last_interaction_at": (
                customer.last_interaction_at.isoformat()
                if customer.last_interaction_at else None
            ),
            "last_visit_at": (
                customer.last_visit_at.isoformat()
                if customer.last_visit_at else None
            ),
            "is_active": customer.is_active,
            "merchant_id": str(customer.merchant_id),
        }
