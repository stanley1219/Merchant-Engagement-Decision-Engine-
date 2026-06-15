from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest

from src.api.v1.schemas.compose import ComposeOutput
from src.rules.engine import rule_engine


@pytest.fixture(autouse=True)
def _reset_rule_engine() -> None:
    rule_engine._rules.clear()
    yield
    rule_engine._rules.clear()


@pytest.fixture
def base_merchant() -> dict[str, Any]:
    return {
        "identity": {
            "merchant_id": "merchant-1",
            "name": "Test Merchant",
            "phone": "+919999999999",
        },
        "category": "dentist",
        "locality": "Andheri West",
        "city": "Mumbai",
        "performance": {
            "review_count": 25,
            "review_score": 4.2,
            "new_members_last_week": 10,
            "usual_weekly_avg": 20,
            "weekend_sales": 0,
        },
        "offers": [],
        "settings": {},
        "is_active": True,
    }


@pytest.fixture
def base_trigger() -> dict[str, Any]:
    return {
        "type": "search_spike",
        "payload": {
            "searches": 100,
            "keyword": "teeth cleaning",
            "locality": "Andheri West",
        },
        "priority": 50,
        "source": "system",
    }


@pytest.fixture
def base_customer() -> dict[str, Any]:
    return {
        "identity": {
            "customer_id": "customer-1",
            "name": "Rahul Sharma",
            "phone": "+919888888888",
        },
        "profile": {
            "days_since_last_visit": 30,
            "lifetime_value": 5000,
            "visit_count": 10,
        },
        "consent": {"sms": True, "whatsapp": True},
        "tags": ["regular"],
    }


@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock()
    redis.delete = AsyncMock()
    redis.exists = AsyncMock()
    redis.expire = AsyncMock()
    redis.ttl = AsyncMock()
    redis.keys = AsyncMock()
    redis.hset = AsyncMock()
    redis.hget = AsyncMock()
    redis.hgetall = AsyncMock()
    redis.hdel = AsyncMock()
    redis.sadd = AsyncMock()
    redis.smembers = AsyncMock()
    redis.sismember = AsyncMock()
    redis.incr = AsyncMock()
    redis.client = MagicMock()
    redis.client.set = AsyncMock()
    redis.client.keys = AsyncMock(return_value=[])
    redis.client.ping = AsyncMock()
    return redis


@pytest.fixture
def mock_llm() -> MagicMock:
    llm = create_autospec(lambda: None)
    llm.compose = AsyncMock(
        return_value=MagicMock(
            message="Polished message",
            cta="Polished CTA",
            send_as="Vera",
            rationale="Polished rationale",
        )
    )
    return llm


@pytest.fixture
def compose_output() -> ComposeOutput:
    return ComposeOutput(
        message="Test message",
        cta="Test CTA",
        send_as="Vera",
        suppression_key="suppression:test_key",
        rationale="Test rationale",
    )


@pytest.fixture
def dentist_search_spike_trigger() -> dict[str, Any]:
    return {
        "type": "search_spike",
        "payload": {
            "searches": 150,
            "keyword": "dental implant",
            "locality": "Bandra",
        },
    }


@pytest.fixture
def salon_lapse_trigger() -> dict[str, Any]:
    return {
        "type": "customer_lapse",
        "payload": {},
    }


@pytest.fixture
def restaurant_sales_dip_trigger() -> dict[str, Any]:
    return {
        "type": "sales_dip",
        "payload": {
            "dip_percent": 25,
            "period": "week",
            "current": 75,
            "usual": 100,
        },
    }


@pytest.fixture
def gym_membership_dip_trigger() -> dict[str, Any]:
    return {
        "type": "membership_dip",
        "payload": {},
    }


@pytest.fixture
def pharmacy_refill_trigger() -> dict[str, Any]:
    return {
        "type": "refill_due",
        "payload": {
            "medication": "Metformin",
            "days_since_last_fill": 45,
            "refills_remaining": 1,
        },
    }
