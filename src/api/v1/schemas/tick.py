from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SignalSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    signal_type: str
    trigger_type: str
    score: float = Field(ge=0, le=100)
    data: Dict[str, Any] = Field(default_factory=dict)
    rationale: str


class ComposeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=500)
    cta: str = Field(min_length=1, max_length=100)
    send_as: str = Field(pattern="^(Vera|merchant)$")
    suppression_key: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ActionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(pattern="^(send_message|schedule|defer|skip)$")
    compose_output: Optional[ComposeOutput] = None
    trigger_id: Optional[str] = None
    delay_seconds: Optional[int] = None
    reason: Optional[str] = None


class TickRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    now: str = ""
    available_triggers: List[str] = Field(default_factory=list)


class TickResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    actions: List[Dict[str, Any]] = Field(default_factory=list)


class MerchantSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    category: str
    locality: Optional[str] = None
    active_triggers: int = 0
    pending_messages: int = 0
    last_tick_at: Optional[datetime] = None
