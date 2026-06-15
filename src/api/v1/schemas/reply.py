from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReplyRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    conversation_id: str = ""
    merchant_id: str = ""
    customer_id: Optional[str] = None
    from_role: str = ""
    message: str = ""
    received_at: str = ""
    turn_number: int = 0


class ReplyResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: str = "send"
    body: Optional[str] = None
    wait_seconds: Optional[int] = None
