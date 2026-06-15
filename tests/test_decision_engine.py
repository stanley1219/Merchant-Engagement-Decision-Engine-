from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.core.constants import Category, SignalType
from src.rules.engine import rule_engine
from src.services.composer.decision_engine import DecisionEngine
from src.services.composer.message_generator import MessageGenerator
from src.services.composer.signal_ranker import rank_signals, select_best_signal
from src.services.composer.suppression_engine import SuppressionEngine
from src.services.composer.template_selector import get_template


@pytest.fixture(autouse=True)
def _register_all_rules() -> None:
    import importlib
    for mod_name in (
        "src.rules.category_rules.dentists",
        "src.rules.category_rules.salons",
        "src.rules.category_rules.restaurants",
        "src.rules.category_rules.gyms",
        "src.rules.category_rules.pharmacies",
    ):
        importlib.reload(importlib.import_module(mod_name))


@pytest.fixture
def mock_suppression(mock_redis: AsyncMock) -> SuppressionEngine:
    engine = SuppressionEngine(mock_redis)
    mock_redis.client.set = AsyncMock(return_value=True)
    return engine


class TestSignalRanker:
    def test_rank_signals_orders_by_score(self) -> None:
        from src.rules.engine import Signal
        from src.core.constants import TriggerType

        signals = [
            Signal(signal_type=SignalType.DEMAND_SPIKE, trigger_type=TriggerType.SEARCH_SPIKE, score=50, data={}, rationale="low"),
            Signal(signal_type=SignalType.DEMAND_SPIKE, trigger_type=TriggerType.SEARCH_SPIKE, score=80, data={}, rationale="high"),
            Signal(signal_type=SignalType.REVENUE_OPPORTUNITY, trigger_type=TriggerType.OFFER_MATCH, score=65, data={}, rationale="medium"),
        ]
        merchant: dict[str, Any] = {"identity": {"merchant_id": "m1"}}
        ranked = rank_signals(signals, merchant, Category.DENTIST)
        assert len(ranked) == 3
        assert ranked[0].final_score >= ranked[1].final_score

    def test_select_best_signal_returns_highest(self) -> None:
        from src.rules.engine import Signal
        from src.core.constants import TriggerType

        signals = [
            Signal(signal_type=SignalType.DEMAND_SPIKE, trigger_type=TriggerType.SEARCH_SPIKE, score=50, data={}, rationale="low"),
            Signal(signal_type=SignalType.REVENUE_OPPORTUNITY, trigger_type=TriggerType.OFFER_MATCH, score=90, data={}, rationale="best"),
        ]
        merchant: dict[str, Any] = {"identity": {"merchant_id": "m1"}}
        best = select_best_signal(signals, merchant, Category.DENTIST)
        assert best is not None
        assert best.signal.score == 90

    def test_rank_signals_tie_break_by_signal_type(self) -> None:
        from src.rules.engine import Signal
        from src.core.constants import TriggerType

        signals = [
            Signal(signal_type=SignalType.REVENUE_OPPORTUNITY, trigger_type=TriggerType.OFFER_MATCH, score=70, data={}, rationale="rev"),
            Signal(signal_type=SignalType.DEMAND_SPIKE, trigger_type=TriggerType.SEARCH_SPIKE, score=70, data={}, rationale="demand"),
        ]
        merchant: dict[str, Any] = {"identity": {"merchant_id": "m1"}}
        ranked = rank_signals(signals, merchant, Category.DENTIST)
        assert ranked[0].signal.signal_type == SignalType.DEMAND_SPIKE  # lower enum value wins

    def test_empty_signals_returns_empty(self) -> None:
        assert rank_signals([], {}, Category.DENTIST) == []
        assert select_best_signal([], {}, Category.DENTIST) is None


class TestTemplateSelector:
    def test_get_template_all_categories_have_templates(self) -> None:
        from src.core.constants import SignalType

        for cat in Category:
            templates_found = 0
            for st in SignalType:
                if get_template(cat, st) is not None:
                    templates_found += 1
            assert templates_found > 0, f"No templates for {cat}"

    def test_unknown_category_returns_none(self) -> None:
        assert get_template("unknown_category", SignalType.DEMAND_SPIKE) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Golden path: each category produces correct SignalType
# ---------------------------------------------------------------------------


class TestDentistGoldenPath:
    @pytest.mark.parametrize(
        ("trigger", "expected_signal_type", "merchant_mods"),
        [
            (
                {
                    "type": "search_spike",
                    "payload": {"searches": 120, "keyword": "dental implant", "locality": "Bandra"},
                },
                SignalType.DEMAND_SPIKE,
                {},
            ),
            (
                {"type": "recall_due", "payload": {}},
                SignalType.RETENTION_RISK,
                {},
            ),
            (
                {"type": "review_request", "payload": {}},
                SignalType.ENGAGEMENT_OPPORTUNITY,
                {"performance": {"review_count": 5, "review_score": 3.5}},
            ),
        ],
    )
    async def test_dentist_decision(
        self,
        trigger: dict[str, Any],
        expected_signal_type: SignalType,
        merchant_mods: dict[str, Any],
        mock_suppression: SuppressionEngine,
    ) -> None:
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "dentist-1"},
            "category": "dentist",
            "performance": {"review_count": 20, "review_score": 4.0},
            "offers": [{"name": "Free Checkup", "price": 0, "is_active": True}],
        }
        merchant.update(merchant_mods)
        customer: dict[str, Any] = {
            "name": "Patient",
            "profile": {"days_since_last_visit": 200},
        }
        engine = DecisionEngine(mock_suppression)
        result = await engine.decide(Category.DENTIST, merchant, trigger, customer)
        assert result is not None, f"No decision for {expected_signal_type}"
        assert result.signal.signal_type == expected_signal_type

    async def test_dentist_no_signal_when_no_match(
        self,
        mock_suppression: SuppressionEngine,
    ) -> None:
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "dentist-1"},
            "category": "dentist",
            "performance": {},
            "offers": [],
        }
        trigger: dict[str, Any] = {
            "type": "search_spike",
            "payload": {"searches": 20, "keyword": "test", "locality": "Mumbai"},
        }
        result = await DecisionEngine(mock_suppression).decide(Category.DENTIST, merchant, trigger)
        assert result is None


class TestSalonGoldenPath:
    async def test_salon_customer_lapse(
        self,
        mock_suppression: SuppressionEngine,
    ) -> None:
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "salon-1"},
            "category": "salon",
            "offers": [],
            "performance": {},
        }
        trigger: dict[str, Any] = {"type": "customer_lapse", "payload": {}}
        customer: dict[str, Any] = {
            "name": "Client",
            "profile": {"days_since_last_visit": 120},
        }
        result = await DecisionEngine(mock_suppression).decide(Category.SALON, merchant, trigger, customer)
        assert result is not None
        assert result.signal.signal_type == SignalType.RETENTION_RISK

    async def test_salon_no_signal_no_customer(
        self,
        mock_suppression: SuppressionEngine,
    ) -> None:
        result = await DecisionEngine(mock_suppression).decide(
            Category.SALON,
            {"identity": {"merchant_id": "s1"}, "category": "salon", "offers": [], "performance": {}},
            {"type": "customer_lapse", "payload": {}},
            None,
        )
        assert result is None


class TestRestaurantGoldenPath:
    async def test_restaurant_sales_dip(
        self,
        mock_suppression: SuppressionEngine,
    ) -> None:
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "rest-1"},
            "category": "restaurant",
            "offers": [],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "sales_dip",
            "payload": {"dip_percent": 30, "period": "week", "current": 70, "usual": 100},
        }
        result = await DecisionEngine(mock_suppression).decide(Category.RESTAURANT, merchant, trigger)
        assert result is not None
        assert result.signal.signal_type == SignalType.ACQUISITION_DIP


class TestGymGoldenPath:
    async def test_gym_membership_dip(
        self,
        mock_suppression: SuppressionEngine,
    ) -> None:
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "gym-1"},
            "category": "gym",
            "offers": [],
            "performance": {"new_members_last_week": 5, "usual_weekly_avg": 20},
        }
        trigger: dict[str, Any] = {"type": "membership_dip", "payload": {}}
        result = await DecisionEngine(mock_suppression).decide(Category.GYM, merchant, trigger)
        assert result is not None
        assert result.signal.signal_type == SignalType.ACQUISITION_DIP


class TestPharmacyGoldenPath:
    async def test_pharmacy_refill_due(
        self,
        mock_suppression: SuppressionEngine,
    ) -> None:
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "pharm-1"},
            "category": "pharmacy",
            "offers": [],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "refill_due",
            "payload": {
                "medication": "Metformin",
                "days_since_last_fill": 45,
                "refills_remaining": 1,
            },
        }
        customer: dict[str, Any] = {"name": "Patient", "profile": {}}
        result = await DecisionEngine(mock_suppression).decide(
            Category.PHARMACY, merchant, trigger, customer
        )
        assert result is not None
        assert result.signal.signal_type == SignalType.RETENTION_RISK

    async def test_pharmacy_compliance_alert(
        self,
        mock_suppression: SuppressionEngine,
    ) -> None:
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "pharm-1"},
            "category": "pharmacy",
            "offers": [],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "compliance_alert",
            "payload": {"alert_type": "License Expiry", "severity": "critical", "deadline": "2026-07-01"},
        }
        result = await DecisionEngine(mock_suppression).decide(Category.PHARMACY, merchant, trigger)
        assert result is not None
        assert result.signal.signal_type == SignalType.OPERATIONAL_ALERT
        assert result.message_template != ""
        assert result.cta_template != ""


class TestDecisionEngineWithSuppression:
    async def test_suppressed_signal_returns_none(
        self,
        mock_redis: AsyncMock,
    ) -> None:
        mock_redis.client.set = AsyncMock(return_value=False)  # key exists -> suppressed
        suppression = SuppressionEngine(mock_redis)
        engine = DecisionEngine(suppression)
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "m1"},
            "category": "dentist",
            "offers": [{"name": "Checkup", "is_active": True}],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "search_spike",
            "payload": {"searches": 100, "keyword": "checkup", "locality": "Mumbai"},
        }
        result = await engine.decide(Category.DENTIST, merchant, trigger)
        assert result is None

    async def test_force_overrides_suppression(
        self,
        mock_redis: AsyncMock,
    ) -> None:
        mock_redis.client.set = AsyncMock(return_value=False)  # already suppressed
        suppression = SuppressionEngine(mock_redis)
        engine = DecisionEngine(suppression)
        merchant: dict[str, Any] = {
            "identity": {"merchant_id": "m1"},
            "category": "dentist",
            "offers": [{"name": "Checkup", "is_active": True}],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "search_spike",
            "payload": {"searches": 100, "keyword": "checkup", "locality": "Mumbai"},
        }
        result = await engine.decide(Category.DENTIST, merchant, trigger, force=True)
        assert result is not None
        assert result.is_suppressed is True  # still True but allowed through


class TestMessageGenerator:
    async def test_generates_direct_output(self, compose_output) -> None:
        from src.rules.engine import Signal
        from src.core.constants import TriggerType

        decision = create_autospec(lambda: None)
        decision.message_template = "Test message"  # Already formatted by DecisionEngine
        decision.cta_template = "Test CTA"
        decision.send_as = "Vera"
        decision.suppression_key = "suppression:test"
        decision.signal = Signal(
            signal_type=SignalType.DEMAND_SPIKE,
            trigger_type=TriggerType.SEARCH_SPIKE,
            score=75,
            data={"name": "test"},
            rationale="Test rationale",
        )
        gen = MessageGenerator()
        output = await gen.generate(decision, "dentist", use_llm=False)
        assert output.message == "Test message"
        assert output.cta == "Test CTA"
        assert output.send_as == "Vera"
        assert output.suppression_key == "suppression:test"
        assert output.rationale == "Test rationale"

    async def test_generates_llm_output(self, mock_llm) -> None:
        from src.rules.engine import Signal
        from src.core.constants import TriggerType

        decision = create_autospec(lambda: None)
        decision.message_template = "Template"
        decision.cta_template = "CTA"
        decision.send_as = "Vera"
        decision.suppression_key = "suppression:k"
        decision.signal = Signal(
            signal_type=SignalType.DEMAND_SPIKE,
            trigger_type=TriggerType.SEARCH_SPIKE,
            score=75,
            data={},
            rationale="r",
        )
        gen = MessageGenerator(llm=mock_llm)
        output = await gen.generate(decision, "dentist", use_llm=True)
        assert output.message == "Polished message"
        assert mock_llm.compose.called


from unittest.mock import create_autospec  # noqa: E402
