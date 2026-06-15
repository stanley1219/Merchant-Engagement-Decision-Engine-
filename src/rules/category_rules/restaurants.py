from typing import Any, Dict, Optional

from src.core.constants import Category, SignalType, TriggerType
from src.rules.engine import BaseRule, Signal, rule_engine


class EventSpikeRule(BaseRule):
    category = Category.RESTAURANT
    trigger_types = [TriggerType.EVENT]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        event_name = trigger.get("payload", {}).get("name", "")
        hours_until = trigger.get("payload", {}).get("hours_until", 24)

        if hours_until > 12:
            return None

        weekend_sales = merchant.get("performance", {}).get("weekend_sales", 0)
        offer = self._find_matching_offer(merchant, ["combo", "family", "group", "party", "match", "ipl"])

        score = 75
        if weekend_sales < 0:
            score = 85
        if offer:
            score = min(90, score + 5)

        return Signal(
            signal_type=SignalType.REVENUE_OPPORTUNITY,
            trigger_type=TriggerType.EVENT,
            score=score,
            data={
                "event": event_name,
                "hours_until": hours_until,
                "weekend_sales": weekend_sales,
                "offer_name": offer.get("name") if offer else None,
                "offer_price": offer.get("price") if offer else None,
            },
            rationale=f"Event '{event_name}' in {hours_until}h" + (f" - sales down {abs(weekend_sales)}%" if weekend_sales < 0 else "") + (f" + {offer.get('name')}" if offer else ""),
        )


class SalesDipRule(BaseRule):
    category = Category.RESTAURANT
    trigger_types = [TriggerType.SALES_DIP]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        payload = trigger.get("payload", {})
        dip_percent = payload.get("dip_percent", 0)
        period = payload.get("period", "week")
        current_val = payload.get("current", 0)
        usual_val = payload.get("usual", 1)

        if dip_percent < 10:
            return None

        offer = self._find_matching_offer(merchant, ["combo", "lunch", "discount", "offer", "deal"])

        score = min(85, 55 + dip_percent)
        return Signal(
            signal_type=SignalType.ACQUISITION_DIP,
            trigger_type=TriggerType.SALES_DIP,
            score=score,
            data={
                "dip_percent": dip_percent,
                "period": period,
                "current": current_val,
                "usual": usual_val,
                "offer_name": offer.get("name") if offer else None,
                "offer_price": offer.get("price") if offer else None,
            },
            rationale=f"Sales down {dip_percent}% this {period}" + (f" - {offer.get('name')} can help recover" if offer else ""),
        )


class NewMenuRule(BaseRule):
    category = Category.RESTAURANT
    trigger_types = [TriggerType.NEW_MENU]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        items = trigger.get("payload", {}).get("items", [])
        if not items:
            return None

        return Signal(
            signal_type=SignalType.ENGAGEMENT_OPPORTUNITY,
            trigger_type=TriggerType.NEW_MENU,
            score=65,
            data={
                "new_items": items[:3],
                "count": len(items),
            },
            rationale=f"New menu launched with {len(items)} items",
        )


class CorporateEnquiryRule(BaseRule):
    category = Category.RESTAURANT
    trigger_types = [TriggerType.CORPORATE_ENQUIRY]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        party_size = trigger.get("payload", {}).get("party_size", 0)
        budget = trigger.get("payload", {}).get("budget_per_head", 0)

        if party_size < 10:
            return None

        offer = self._find_matching_offer(merchant, ["corporate", "thali", "buffet", "group", "party"])

        score = min(80, 50 + (party_size // 5))
        return Signal(
            signal_type=SignalType.REVENUE_OPPORTUNITY,
            trigger_type=TriggerType.CORPORATE_ENQUIRY,
            score=score,
            data={
                "party_size": party_size,
                "budget_per_head": budget,
                "offer_name": offer.get("name") if offer else None,
                "offer_price": offer.get("price") if offer else None,
            },
            rationale=f"Corporate enquiry for {party_size} people @ ₹{budget}/head" + (f" - {offer.get('name')} fits" if offer else ""),
        )


rule_engine.register(Category.RESTAURANT, EventSpikeRule())
rule_engine.register(Category.RESTAURANT, SalesDipRule())
rule_engine.register(Category.RESTAURANT, NewMenuRule())
rule_engine.register(Category.RESTAURANT, CorporateEnquiryRule())