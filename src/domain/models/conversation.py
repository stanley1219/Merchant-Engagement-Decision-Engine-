from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import BaseModel


class Conversation(BaseModel):
    __tablename__ = "conversations"

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
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    context: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    suppression_keys: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    message_count: Mapped[int] = mapped_column(nullable=False, default=0)
    extra_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="conversations")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="conversations")

    __table_args__ = (
        Index("ix_conversations_merchant_state", "merchant_id", "state"),
        Index("ix_conversations_customer", "customer_id"),
    )

    def add_suppression_key(self, key: str) -> None:
        if key not in self.suppression_keys:
            self.suppression_keys.append(key)

    def has_suppression_key(self, key: str) -> bool:
        return key in self.suppression_keys

    def update_last_message(self, timestamp: datetime) -> None:
        self.last_message_at = timestamp
        self.message_count += 1


class MessageLog(BaseModel):
    __tablename__ = "message_logs"

    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trigger_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("triggers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    conversation_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    output: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="sent")
    delivery_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="message_logs")
    trigger: Mapped[Optional["Trigger"]] = relationship("Trigger", back_populates="message_logs")

    __table_args__ = (
        Index("ix_message_logs_merchant_sent", "merchant_id", "sent_at"),
        Index("ix_message_logs_signal", "signal_type"),
    )