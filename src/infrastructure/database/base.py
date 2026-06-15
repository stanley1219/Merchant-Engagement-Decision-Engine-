from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import DateTime, func, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )


class JSONBMixin:
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        table = getattr(self, "__table__", None)
        if table is not None:
            for column in table.columns:  # type: ignore[attr-defined]
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                elif hasattr(value, "to_dict"):
                    result[column.name] = value.to_dict()
                else:
                    result[column.name] = value
        return result


class BaseModel(Base, UUIDMixin, TimestampMixin):
    __abstract__ = True