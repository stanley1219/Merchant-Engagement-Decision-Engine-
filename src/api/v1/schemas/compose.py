from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComposeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    merchant: Dict[str, Any]
    trigger: Dict[str, Any]
    customer: Optional[Dict[str, Any]] = None


class ComposeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=500)
    cta: str = Field(min_length=1, max_length=100)
    send_as: str = Field(pattern="^(Vera|merchant)$")
    suppression_key: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ComposeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output: ComposeOutput
    signal_used: str
    confidence: float = Field(ge=0, le=1)