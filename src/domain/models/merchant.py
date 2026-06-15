from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import BaseModel


class Merchant(BaseModel):
    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    locality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    identity: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    performance_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    offers: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    settings: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    last_context_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    customers: Mapped[List["Customer"]] = relationship(
        "Customer",
        back_populates="merchant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    triggers: Mapped[List["Trigger"]] = relationship(
        "Trigger",
        back_populates="merchant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="merchant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    message_logs: Mapped[List["MessageLog"]] = relationship(
        "MessageLog",
        back_populates="merchant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_merchants_category_locality", "category", "locality"),
        Index("ix_merchants_version", "version"),
        UniqueConstraint("phone", name="uq_merchant_phone"),
    )

    def get_active_offers(self) -> List[Dict[str, Any]]:
        return [o for o in self.offers if o.get("is_active", True)]

    def get_metric(self, key: str, default: Any = None) -> Any:
        return self.performance_metrics.get(key, default)

    def set_metric(self, key: str, value: Any) -> None:
        self.performance_metrics[key] = value