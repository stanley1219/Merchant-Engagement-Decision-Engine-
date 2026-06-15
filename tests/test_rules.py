from __future__ import annotations

from typing import Any

import pytest

from src.core.constants import Category, SignalType, TriggerType
from src.rules.category_rules.dentists import (
    OfferMatchRule,
    RecallDueRule,
    ReviewRequestRule,
    SearchSpikeRule,
)
from src.rules.category_rules.gyms import (
    ClassWaitlistRule,
    MembershipDipRule,
    SeasonalSurgeRule,
    TrialConversionRule,
)
from src.rules.category_rules.pharmacies import (
    ChronicCareRule,
    ComplianceAlertRule,
    RefillDueRule,
    StockAlertRule,
)
from src.rules.category_rules.restaurants import (
    CorporateEnquiryRule,
    EventSpikeRule,
    NewMenuRule,
    SalesDipRule,
)
from src.rules.category_rules.salons import (
    BridalFollowupRule,
    CustomerLapseRule,
    SeasonalTrendRule,
    StylistAvailabilityRule,
)
from src.rules.engine import rule_engine

# ---------------------------------------------------------------------------
# Dentist rules
# ---------------------------------------------------------------------------


class TestSearchSpikeRule:
    def setup_method(self) -> None:
        self.rule = SearchSpikeRule()

    def test_high_searches_with_offer(self) -> None:
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "Free Dental Checkup",
                    "price": 0,
                    "is_active": True,
                    "description": "Basic dental checkup",
                }
            ],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "search_spike",
            "payload": {
                "searches": 120,
                "keyword": "checkup",
                "locality": "Andheri",
            },
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.DEMAND_SPIKE
        assert signal.score >= 70
        assert signal.score <= 90
        assert "offer_name" in signal.data
        assert signal.data["offer_name"] == "Free Dental Checkup"

    def test_high_searches_no_offer(self) -> None:
        merchant: dict[str, Any] = {"offers": [], "performance": {}}
        trigger: dict[str, Any] = {
            "type": "search_spike",
            "payload": {
                "searches": 120,
                "keyword": "root canal",
                "locality": "Bandra",
            },
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.DEMAND_SPIKE
        assert signal.score <= 70
        assert "offer_name" not in signal.data

    def test_low_searches_no_signal(self) -> None:
        merchant: dict[str, Any] = {"offers": [], "performance": {}}
        trigger: dict[str, Any] = {
            "type": "search_spike",
            "payload": {"searches": 20, "keyword": "teeth", "locality": "Mumbai"},
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is None

    def test_ignores_wrong_trigger_type(self) -> None:
        assert TriggerType.SEARCH_SPIKE in self.rule.trigger_types
        assert TriggerType.RECALL_DUE not in self.rule.trigger_types


class TestRecallDueRule:
    def setup_method(self) -> None:
        self.rule = RecallDueRule()

    def test_overdue_patient_returns_signal(self) -> None:
        customer: dict[str, Any] = {
            "name": "Priya Patel",
            "profile": {"days_since_last_visit": 200},
        }
        signal = self.rule.evaluate({}, {"type": "recall_due"}, customer)
        assert signal is not None
        assert signal.signal_type == SignalType.RETENTION_RISK
        assert signal.score == 75
        assert signal.data["customer_name"] == "Priya Patel"

    def test_recent_visit_no_signal(self) -> None:
        customer: dict[str, Any] = {
            "name": "Priya Patel",
            "profile": {"days_since_last_visit": 90},
        }
        signal = self.rule.evaluate({}, {"type": "recall_due"}, customer)
        assert signal is None

    def test_no_customer_no_signal(self) -> None:
        signal = self.rule.evaluate({}, {"type": "recall_due"}, None)
        assert signal is None


class TestReviewRequestRule:
    def setup_method(self) -> None:
        self.rule = ReviewRequestRule()

    def test_few_reviews_high_score(self) -> None:
        merchant: dict[str, Any] = {
            "performance": {"review_count": 5, "review_score": 4.5}
        }
        signal = self.rule.evaluate(merchant, {"type": "review_request"})
        assert signal is not None
        assert signal.signal_type == SignalType.ENGAGEMENT_OPPORTUNITY
        assert signal.score == 65

    def test_low_score_higher_priority(self) -> None:
        merchant: dict[str, Any] = {
            "performance": {"review_count": 20, "review_score": 3.5}
        }
        signal = self.rule.evaluate(merchant, {"type": "review_request"})
        assert signal is not None
        assert signal.score == 70

    def test_high_reviews_good_score(self) -> None:
        merchant: dict[str, Any] = {
            "performance": {"review_count": 50, "review_score": 4.8}
        }
        signal = self.rule.evaluate(merchant, {"type": "review_request"})
        assert signal is not None
        assert signal.score == 55


class TestOfferMatchRule:
    def setup_method(self) -> None:
        self.rule = OfferMatchRule()

    def test_matching_offer_returns_signal(self) -> None:
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "Teeth Whitening Special",
                    "price": 4999,
                    "is_active": True,
                    "description": "Professional teeth whitening",
                }
            ],
            "performance": {},
        }
        signal = self.rule.evaluate(merchant, {"type": "offer_match"})
        assert signal is not None
        assert signal.signal_type == SignalType.REVENUE_OPPORTUNITY
        assert signal.score == 60

    def test_no_matching_offer_no_signal(self) -> None:
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "Haircut Special",
                    "price": 299,
                    "is_active": True,
                    "description": "Stylish haircut",
                }
            ],
            "performance": {},
        }
        signal = self.rule.evaluate(merchant, {"type": "offer_match"})
        assert signal is None

    def test_inactive_offer_not_match(self) -> None:
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "Teeth Whitening",
                    "price": 4999,
                    "is_active": False,
                    "description": "Whitening",
                }
            ],
            "performance": {},
        }
        signal = self.rule.evaluate(merchant, {"type": "offer_match"})
        assert signal is None


# ---------------------------------------------------------------------------
# Salon rules
# ---------------------------------------------------------------------------


class TestCustomerLapseRule:
    def setup_method(self) -> None:
        self.rule = CustomerLapseRule()

    def test_lapsed_customer_with_offer(self) -> None:
        customer: dict[str, Any] = {
            "name": "Anjali Mehta",
            "profile": {"days_since_last_visit": 120},
        }
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "Hair Spa Discount",
                    "price": 999,
                    "is_active": True,
                    "description": "Hair spa at 50% off",
                }
            ],
            "performance": {},
        }
        signal = self.rule.evaluate(merchant, {"type": "customer_lapse"}, customer)
        assert signal is not None
        assert signal.signal_type == SignalType.RETENTION_RISK
        assert signal.score == 55 + (120 // 30)
        assert signal.data["offer_name"] == "Hair Spa Discount"

    def test_lapsed_customer_no_offer(self) -> None:
        customer: dict[str, Any] = {
            "name": "Anjali Mehta",
            "profile": {"days_since_last_visit": 120},
        }
        signal = self.rule.evaluate({}, {"type": "customer_lapse"}, customer)
        assert signal is not None
        assert signal.data["offer_name"] is None

    def test_recent_visit_no_signal(self) -> None:
        customer: dict[str, Any] = {
            "name": "Anjali Mehta",
            "profile": {"days_since_last_visit": 30},
        }
        signal = self.rule.evaluate({}, {"type": "customer_lapse"}, customer)
        assert signal is None

    def test_no_customer_no_signal(self) -> None:
        signal = self.rule.evaluate({}, {"type": "customer_lapse"}, None)
        assert signal is None


class TestBridalFollowupRule:
    def setup_method(self) -> None:
        self.rule = BridalFollowupRule()

    def test_bridal_customer_returns_signal(self) -> None:
        customer: dict[str, Any] = {
            "name": "Sneha Kapoor",
            "profile": {"wedding_date": "2026-12-15"},
        }
        signal = self.rule.evaluate({}, {"type": "bridal_followup"}, customer)
        assert signal is not None
        assert signal.signal_type == SignalType.ENGAGEMENT_OPPORTUNITY
        assert signal.score == 80
        assert signal.data["wedding_date"] == "2026-12-15"

    def test_no_wedding_date_no_signal(self) -> None:
        customer: dict[str, Any] = {
            "name": "Sneha Kapoor",
            "profile": {},
        }
        signal = self.rule.evaluate({}, {"type": "bridal_followup"}, customer)
        assert signal is None

    def test_no_customer_no_signal(self) -> None:
        signal = self.rule.evaluate({}, {"type": "bridal_followup"}, None)
        assert signal is None


class TestSeasonalTrendRule:
    def setup_method(self) -> None:
        self.rule = SeasonalTrendRule()

    def test_matching_trend_offer(self) -> None:
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "Summer Glow Facial",
                    "price": 1499,
                    "is_active": True,
                    "description": "Get that summer glow",
                }
            ],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "seasonal_trend",
            "payload": {"trend": "glow", "season": "summer"},
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.REVENUE_OPPORTUNITY
        assert signal.score == 70

    def test_no_matching_offer_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "seasonal_trend",
            "payload": {"trend": "bridal", "season": "winter"},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None


class TestStylistAvailabilityRule:
    def setup_method(self) -> None:
        self.rule = StylistAvailabilityRule()

    def test_enough_slots_returns_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "stylist_availability",
            "payload": {"stylist_name": "Neha", "available_slots": 5},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.REVENUE_OPPORTUNITY
        assert signal.score == 65

    def test_few_slots_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "stylist_availability",
            "payload": {"stylist_name": "Neha", "available_slots": 1},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None


# ---------------------------------------------------------------------------
# Restaurant rules
# ---------------------------------------------------------------------------


class TestEventSpikeRule:
    def setup_method(self) -> None:
        self.rule = EventSpikeRule()

    def test_event_within_window_returns_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "event",
            "payload": {"name": "IPL Match", "hours_until": 6},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.REVENUE_OPPORTUNITY
        assert signal.score == 75

    def test_event_too_far_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "event",
            "payload": {"name": "IPL Match", "hours_until": 24},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None

    def test_event_with_sales_dip_boosts_score(self) -> None:
        merchant: dict[str, Any] = {
            "performance": {"weekend_sales": -15},
            "offers": [],
        }
        trigger: dict[str, Any] = {
            "type": "event",
            "payload": {"name": "IPL Match", "hours_until": 4},
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is not None
        assert signal.score == 85

    def test_event_with_matching_offer_boosts_score(self) -> None:
        merchant: dict[str, Any] = {
            "performance": {"weekend_sales": 0},
            "offers": [
                {
                    "name": "IPL Combo Offer",
                    "price": 599,
                    "is_active": True,
                    "description": "Match day combo",
                }
            ],
        }
        trigger: dict[str, Any] = {
            "type": "event",
            "payload": {"name": "IPL Match", "hours_until": 4},
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is not None
        assert signal.score == 80
        assert signal.data["offer_name"] == "IPL Combo Offer"


class TestSalesDipRule:
    def setup_method(self) -> None:
        self.rule = SalesDipRule()

    def test_significant_dip_with_offer(self) -> None:
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "Lunch Combo Deal",
                    "price": 299,
                    "is_active": True,
                    "description": "Affordable lunch combo",
                }
            ],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "sales_dip",
            "payload": {"dip_percent": 30, "period": "week", "current": 70, "usual": 100},
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.ACQUISITION_DIP
        assert signal.score == min(85, 55 + 30)

    def test_small_dip_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "sales_dip",
            "payload": {"dip_percent": 5, "period": "week", "current": 95, "usual": 100},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None


class TestNewMenuRule:
    def setup_method(self) -> None:
        self.rule = NewMenuRule()

    def test_new_items_returns_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "new_menu",
            "payload": {
                "items": [
                    {"name": "Truffle Pasta", "price": 450},
                    {"name": "Grilled Salmon", "price": 650},
                ]
            },
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.ENGAGEMENT_OPPORTUNITY
        assert signal.score == 65
        assert signal.data["count"] == 2

    def test_no_items_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "new_menu",
            "payload": {"items": []},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None


class TestCorporateEnquiryRule:
    def setup_method(self) -> None:
        self.rule = CorporateEnquiryRule()

    def test_large_party_returns_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "corporate_enquiry",
            "payload": {"party_size": 50, "budget_per_head": 800},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.REVENUE_OPPORTUNITY
        assert signal.score == 60

    def test_small_party_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "corporate_enquiry",
            "payload": {"party_size": 5, "budget_per_head": 500},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None

    def test_large_party_with_matching_offer(self) -> None:
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "Corporate Buffet Deal",
                    "price": 699,
                    "is_active": True,
                    "description": "Best for groups",
                }
            ],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "corporate_enquiry",
            "payload": {"party_size": 30, "budget_per_head": 700},
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is not None
        assert signal.data["offer_name"] == "Corporate Buffet Deal"


# ---------------------------------------------------------------------------
# Gym rules
# ---------------------------------------------------------------------------


class TestMembershipDipRule:
    def setup_method(self) -> None:
        self.rule = MembershipDipRule()

    def test_significant_dip_returns_signal(self) -> None:
        merchant: dict[str, Any] = {
            "performance": {"new_members_last_week": 5, "usual_weekly_avg": 20},
        }
        signal = self.rule.evaluate(merchant, {"type": "membership_dip"})
        assert signal is not None
        assert signal.signal_type == SignalType.ACQUISITION_DIP
        dip_pct = round((1 - 5 / 20) * 100)
        assert signal.score == min(85, 55 + dip_pct)

    def test_no_dip_no_signal(self) -> None:
        merchant: dict[str, Any] = {
            "performance": {"new_members_last_week": 18, "usual_weekly_avg": 20},
        }
        signal = self.rule.evaluate(merchant, {"type": "membership_dip"})
        assert signal is None

    def test_zero_usual_avg_no_signal(self) -> None:
        merchant: dict[str, Any] = {
            "performance": {"new_members_last_week": 5, "usual_weekly_avg": 0},
        }
        signal = self.rule.evaluate(merchant, {"type": "membership_dip"})
        assert signal is None


class TestTrialConversionRule:
    def setup_method(self) -> None:
        self.rule = TrialConversionRule()

    def test_low_conversion_returns_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "trial_conversion",
            "payload": {"active_trials": 20, "conversion_rate": 15},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.REVENUE_OPPORTUNITY
        assert signal.score == 70

    def test_few_trials_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "trial_conversion",
            "payload": {"active_trials": 3, "conversion_rate": 10},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None

    def test_high_conversion_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "trial_conversion",
            "payload": {"active_trials": 20, "conversion_rate": 50},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None


class TestSeasonalSurgeRule:
    def setup_method(self) -> None:
        self.rule = SeasonalSurgeRule()

    def test_surge_with_offer(self) -> None:
        merchant: dict[str, Any] = {
            "offers": [
                {
                    "name": "New Year Transformation",
                    "price": 9999,
                    "is_active": True,
                    "description": "Get fit this new year",
                }
            ],
            "performance": {},
        }
        trigger: dict[str, Any] = {
            "type": "seasonal_surge",
            "payload": {"season": "new year", "expected_increase": 40},
        }
        signal = self.rule.evaluate(merchant, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.DEMAND_SPIKE
        assert signal.score == min(80, 50 + 40)

    def test_surge_no_offer(self) -> None:
        trigger: dict[str, Any] = {
            "type": "seasonal_surge",
            "payload": {"season": "summer", "expected_increase": 30},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.data["offer_name"] is None


class TestClassWaitlistRule:
    def setup_method(self) -> None:
        self.rule = ClassWaitlistRule()

    def test_long_waitlist_returns_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "class_waitlist",
            "payload": {"class_name": "Yoga Flow", "waitlist_count": 12},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.REVENUE_OPPORTUNITY
        assert signal.score == 75

    def test_short_waitlist_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "class_waitlist",
            "payload": {"class_name": "Yoga Flow", "waitlist_count": 3},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None


# ---------------------------------------------------------------------------
# Pharmacy rules
# ---------------------------------------------------------------------------


class TestRefillDueRule:
    def setup_method(self) -> None:
        self.rule = RefillDueRule()

    def test_overdue_refill_returns_signal(self) -> None:
        customer: dict[str, Any] = {
            "name": "Amit Kumar",
            "profile": {},
        }
        trigger: dict[str, Any] = {
            "type": "refill_due",
            "payload": {
                "medication": "Metformin",
                "days_since_last_fill": 30,
                "refills_remaining": 2,
            },
        }
        signal = self.rule.evaluate({}, trigger, customer)
        assert signal is not None
        assert signal.signal_type == SignalType.RETENTION_RISK
        assert signal.score == min(85, 55 + (30 // 3))

    def test_recent_fill_no_signal(self) -> None:
        customer: dict[str, Any] = {"name": "Amit Kumar", "profile": {}}
        trigger: dict[str, Any] = {
            "type": "refill_due",
            "payload": {
                "medication": "Metformin",
                "days_since_last_fill": 3,
                "refills_remaining": 2,
            },
        }
        signal = self.rule.evaluate({}, trigger, customer)
        assert signal is None

    def test_no_refills_remaining_boosts_score(self) -> None:
        customer: dict[str, Any] = {"name": "Amit Kumar", "profile": {}}
        trigger: dict[str, Any] = {
            "type": "refill_due",
            "payload": {
                "medication": "Metformin",
                "days_since_last_fill": 30,
                "refills_remaining": 0,
            },
        }
        signal = self.rule.evaluate({}, trigger, customer)
        assert signal is not None
        assert signal.score >= 80

    def test_no_customer_no_signal(self) -> None:
        signal = self.rule.evaluate({}, {"type": "refill_due"}, None)
        assert signal is None


class TestComplianceAlertRule:
    def setup_method(self) -> None:
        self.rule = ComplianceAlertRule()

    def test_critical_alert_returns_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "compliance_alert",
            "payload": {
                "alert_type": "License Expiry",
                "severity": "critical",
                "deadline": "2026-07-01",
            },
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.OPERATIONAL_ALERT
        assert signal.score == 95

    def test_low_severity_returns_lower_score(self) -> None:
        trigger: dict[str, Any] = {
            "type": "compliance_alert",
            "payload": {
                "alert_type": "Staff Training Due",
                "severity": "low",
                "deadline": "",
            },
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.score == 40

    def test_no_alert_type_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "compliance_alert",
            "payload": {"severity": "high", "deadline": ""},
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None


class TestChronicCareRule:
    def setup_method(self) -> None:
        self.rule = ChronicCareRule()

    def test_low_adherence_overdue_consultation(self) -> None:
        customer: dict[str, Any] = {"name": "Sunita Devi", "profile": {}}
        trigger: dict[str, Any] = {
            "type": "chronic_care",
            "payload": {
                "condition": "Diabetes",
                "days_since_consultation": 200,
                "adherence_score": 60,
            },
        }
        signal = self.rule.evaluate({}, trigger, customer)
        assert signal is not None
        assert signal.signal_type == SignalType.ENGAGEMENT_OPPORTUNITY
        assert signal.score == min(85, 50 + 25 + 20)

    def test_good_adherence_recent_consultation_no_signal(self) -> None:
        customer: dict[str, Any] = {"name": "Sunita Devi", "profile": {}}
        trigger: dict[str, Any] = {
            "type": "chronic_care",
            "payload": {
                "condition": "Diabetes",
                "days_since_consultation": 30,
                "adherence_score": 95,
            },
        }
        signal = self.rule.evaluate({}, trigger, customer)
        assert signal is None

    def test_no_condition_no_signal(self) -> None:
        customer: dict[str, Any] = {"name": "Sunita Devi", "profile": {}}
        trigger: dict[str, Any] = {
            "type": "chronic_care",
            "payload": {
                "days_since_consultation": 100,
                "adherence_score": 75,
            },
        }
        signal = self.rule.evaluate({}, trigger, customer)
        assert signal is None

    def test_no_customer_no_signal(self) -> None:
        signal = self.rule.evaluate({}, {"type": "chronic_care"}, None)
        assert signal is None


class TestStockAlertRule:
    def setup_method(self) -> None:
        self.rule = StockAlertRule()

    def test_below_reorder_level_returns_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "stock_alert",
            "payload": {
                "medication": "Amoxicillin",
                "current_stock": 5,
                "reorder_level": 20,
                "demand_forecast": 15,
            },
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.signal_type == SignalType.REVENUE_OPPORTUNITY
        assert signal.score >= 50
        assert signal.score <= 90

    def test_above_reorder_level_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "stock_alert",
            "payload": {
                "medication": "Amoxicillin",
                "current_stock": 30,
                "reorder_level": 20,
                "demand_forecast": 15,
            },
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None

    def test_no_medication_no_signal(self) -> None:
        trigger: dict[str, Any] = {
            "type": "stock_alert",
            "payload": {
                "current_stock": 5,
                "reorder_level": 20,
                "demand_forecast": 15,
            },
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is None

    def test_zero_stock_high_score(self) -> None:
        trigger: dict[str, Any] = {
            "type": "stock_alert",
            "payload": {
                "medication": "Paracetamol",
                "current_stock": 0,
                "reorder_level": 50,
                "demand_forecast": 30,
            },
        }
        signal = self.rule.evaluate({}, trigger)
        assert signal is not None
        assert signal.score >= 85


# ---------------------------------------------------------------------------
# Rule engine integration
# ---------------------------------------------------------------------------


class TestRuleEngineRegistration:
    def _reload_rules(self, *mod_names: str) -> None:
        import importlib
        for name in mod_names:
            importlib.reload(importlib.import_module(name))

    def test_registers_and_evaluates_all_dentist_rules(self) -> None:
        self._reload_rules("src.rules.category_rules.dentists")
        rules = rule_engine.get_rules(Category.DENTIST)
        assert len(rules) == 4

    def test_registers_and_evaluates_all_salon_rules(self) -> None:
        self._reload_rules("src.rules.category_rules.salons")
        rules = rule_engine.get_rules(Category.SALON)
        assert len(rules) == 4

    def test_registers_and_evaluates_all_restaurant_rules(self) -> None:
        self._reload_rules("src.rules.category_rules.restaurants")
        rules = rule_engine.get_rules(Category.RESTAURANT)
        assert len(rules) == 4

    def test_registers_and_evaluates_all_gym_rules(self) -> None:
        self._reload_rules("src.rules.category_rules.gyms")
        rules = rule_engine.get_rules(Category.GYM)
        assert len(rules) == 4

    def test_registers_and_evaluates_all_pharmacy_rules(self) -> None:
        self._reload_rules("src.rules.category_rules.pharmacies")
        rules = rule_engine.get_rules(Category.PHARMACY)
        assert len(rules) == 4

    def test_evaluate_all_with_matching_trigger(self) -> None:
        self._reload_rules("src.rules.category_rules.dentists")
        merchant: dict[str, Any] = {
            "offers": [{"name": "Free Checkup", "is_active": True}],
            "performance": {"review_count": 5, "review_score": 4.0},
        }
        trigger: dict[str, Any] = {
            "type": "search_spike",
            "payload": {"searches": 100, "keyword": "checkup", "locality": "Mumbai"},
        }
        signals = rule_engine.evaluate_all(Category.DENTIST, merchant, trigger)
        assert len(signals) == 1
        assert signals[0].signal_type == SignalType.DEMAND_SPIKE
