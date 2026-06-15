from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "healthy"
    version: str
    timestamp: str
    dependencies: Dict[str, str] = {}


class MetadataResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "Vera Message Engine"
    version: str
    description: str = "Deterministic message composition for merchant growth"
    team_name: str = "Vera Team"
    model: str = "deterministic-rules"
    capabilities: List[str] = [
        "context_management",
        "tick_processing",
        "message_composition",
        "reply_handling",
        "suppression",
    ]
    categories: List[str] = [
        "dentist",
        "salon",
        "restaurant",
        "gym",
        "pharmacy",
    ]
    trigger_types: List[str] = [
        "search_spike",
        "performance_dip",
        "customer_lapse",
        "refill_due",
        "event",
        "recall_due",
        "review_request",
        "offer_match",
        "bridal_followup",
        "seasonal_trend",
        "stylist_availability",
        "sales_dip",
        "new_menu",
        "corporate_enquiry",
        "membership_dip",
        "trial_conversion",
        "seasonal_surge",
        "class_waitlist",
        "compliance_alert",
        "chronic_care",
        "stock_alert",
        "research_digest",
        "festival",
    ]
    limits: Dict[str, Any] = {
        "max_message_length": 500,
        "max_cta_length": 100,
        "max_actions_per_tick": 20,
        "max_context_size_kb": 500,
        "tick_timeout_seconds": 30,
    }
