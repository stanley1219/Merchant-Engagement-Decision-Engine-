from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    profile: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    consent_flags: Mapped[Dict[str, bool]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    tags: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_visit_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    lifetime_value: Mapped[float] = mapped_column(nullable=False, default=0.0)
    visit_count: Mapped[int] = mapped_column(nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="customers")
    customer_triggers: Mapped[List["Trigger"]] = relationship(
        "Trigger",
        back_populates="customer",
        lazy="selectin",
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_customers_merchant_phone", "merchant_id", "phone"),
        Index("ix_customers_merchant_external", "merchant_id", "external_id"),
        Index("ix_customers_last_visit", "last_visit_at"),
    )

    def has_consent(self, channel: str) -> bool:
        return self.consent_flags.get(channel, False)

    def get_profile_value(self, key: str, default: Any = None) -> Any:
        return self.profile.get(key, default)

    def days_since_last_visit(self) -> Optional[int]:
        if not self.last_visit_at:
            return None
        return (datetime.now(self.last_visit_at.tzinfo) - self.last_visit_at).days