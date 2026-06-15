from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import BaseModel


class Trigger(BaseModel):
    __tablename__ = "triggers"

    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="triggers")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="customer_triggers")
    message_logs: Mapped[List["MessageLog"]] = relationship(
        "MessageLog",
        back_populates="trigger",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_triggers_merchant_status", "merchant_id", "status"),
        Index("ix_triggers_type_status", "type", "status"),
        Index("ix_triggers_expires", "expires_at"),
    )

    def get_payload_value(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at