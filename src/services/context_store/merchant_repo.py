from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.domain.models.merchant import Merchant
from src.infrastructure.database.session import get_session


class MerchantRepository:
    async def get_by_id(self, merchant_id: UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            result = await session.execute(
                select(Merchant).where(Merchant.id == merchant_id)
            )
            merchant = result.scalar_one_or_none()
            if not merchant:
                return None
            return self._to_dict(merchant)

    async def get_by_phone(self, phone: str) -> dict[str, Any] | None:
        async with get_session() as session:
            result = await session.execute(
                select(Merchant).where(Merchant.phone == phone)
            )
            merchant = result.scalar_one_or_none()
            if not merchant:
                return None
            return self._to_dict(merchant)

    async def get_by_category(
        self,
        category: str,
        locality: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            stmt = select(Merchant).where(
                Merchant.category == category,
                Merchant.is_active.is_(True),
            )
            if locality:
                stmt = stmt.where(Merchant.locality == locality)
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return [self._to_dict(m) for m in result.scalars().all()]

    async def upsert(
        self,
        scope: str,
        context_id: str,
        version: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        async with get_session() as session:
            if scope == "merchant":
                identity = payload.get("identity", {})
                stmt = pg_insert(Merchant).values(
                    name=identity.get("name", "Unknown"),
                    category=payload.get("category", ""),
                    phone=identity.get("phone", context_id),
                    email=identity.get("email"),
                    address=payload.get("address"),
                    locality=payload.get("locality"),
                    city=payload.get("city"),
                    state=payload.get("state"),
                    identity=identity,
                    performance_metrics=payload.get("performance_metrics", {}),
                    offers=payload.get("offers", []),
                    settings=payload.get("settings", {}),
                    version=version,
                    last_context_update=datetime.now(UTC),
                )
                upsert_stmt = stmt.on_conflict_do_update(
                    constraint="uq_merchant_phone",
                    set_={
                        "name": stmt.excluded.name,
                        "category": stmt.excluded.category,
                        "email": stmt.excluded.email,
                        "address": stmt.excluded.address,
                        "locality": stmt.excluded.locality,
                        "city": stmt.excluded.city,
                        "state": stmt.excluded.state,
                        "identity": stmt.excluded.identity,
                        "performance_metrics": stmt.excluded.performance_metrics,
                        "offers": stmt.excluded.offers,
                        "settings": stmt.excluded.settings,
                        "version": stmt.excluded.version,
                        "last_context_update": stmt.excluded.last_context_update,
                    },
                )
                await session.execute(upsert_stmt)
                await session.commit()

                phone = identity.get("phone", context_id)
                return await self.get_by_phone(phone)

            if scope == "customer":
                raise NotImplementedError("Customer upsert via MerchantRepository")

            raise ValueError(f"Unknown scope: {scope}")

    async def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            stmt = select(Merchant).where(
                or_(
                    Merchant.name.ilike(f"%{query}%"),
                    Merchant.phone.ilike(f"%{query}%"),
                    Merchant.locality.ilike(f"%{query}%"),
                ),
                Merchant.is_active.is_(True),
            )
            if category:
                stmt = stmt.where(Merchant.category == category)
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return [self._to_dict(m) for m in result.scalars().all()]

    def _to_dict(self, merchant: Merchant) -> dict[str, Any]:
        return {
            "identity": {
                "merchant_id": str(merchant.id),
                "name": merchant.name,
                "phone": merchant.phone,
                "email": merchant.email,
            },
            "category": merchant.category,
            "address": merchant.address,
            "locality": merchant.locality,
            "city": merchant.city,
            "state": merchant.state,
            "performance": dict(merchant.performance_metrics),
            "offers": list(merchant.offers),
            "settings": dict(merchant.settings),
            "version": merchant.version,
            "is_active": merchant.is_active,
            "created_at": merchant.created_at.isoformat() if merchant.created_at else None,
            "updated_at": merchant.updated_at.isoformat() if merchant.updated_at else None,
        }
