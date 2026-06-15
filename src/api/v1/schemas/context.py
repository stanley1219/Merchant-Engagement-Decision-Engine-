from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IdentitySchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    category: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class PerformanceMetricsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    monthly_bookings: Optional[int] = None
    weekly_bookings: Optional[int] = None
    weekend_sales: Optional[float] = None
    new_members_last_week: Optional[int] = None
    usual_weekly_avg: Optional[int] = None
    average_order_value: Optional[float] = None
    repeat_rate: Optional[float] = None
    review_score: Optional[float] = None
    review_count: Optional[int] = None


class OfferSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str = ""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percent: Optional[float] = None
    is_active: bool = True
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    category: Optional[str] = None
    tags: List[str] = []


class MerchantContextPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    identity: IdentitySchema
    performance: PerformanceMetricsSchema = Field(default_factory=PerformanceMetricsSchema)
    offers: List[OfferSchema] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)


class CustomerContextPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    merchant_id: str
    external_id: Optional[str] = None
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    profile: Dict[str, Any] = Field(default_factory=dict)
    consent_flags: Dict[str, bool] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    last_visit_at: Optional[datetime] = None
    lifetime_value: float = 0.0
    visit_count: int = 0


class TriggerContextPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    merchant_id: str = ""
    customer_id: Optional[str] = None
    type: str = ""
    kind: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 50
    source: str = "system"
    expires_at: Optional[datetime] = None


class ContextRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    scope: str
    context_id: str
    version: int = 1
    payload: Dict[str, Any] = Field(default_factory=dict)
    delivered_at: Optional[datetime] = None


class ContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool
    ack_id: str
    stored_at: datetime


class ContextVersionInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context_id: str
    scope: str
    version: int
    updated_at: datetime
