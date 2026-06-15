from typing import Any, Dict, Optional

from src.core.constants import Category, SignalType, TriggerType
from src.rules.engine import BaseRule, Signal, rule_engine


class CustomerLapseRule(BaseRule):
    category = Category.SALON
    trigger_types = [TriggerType.CUSTOMER_LAPSE]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        if not customer:
            return None

        days_since = customer.get("profile", {}).get("days_since_last_visit", 0)
        if days_since < 60:
            return None

        offer = self._find_matching_offer(merchant, ["hair spa", "facial", "cut", "color", "bridal"])

        score = min(85, 55 + (days_since // 30))
        return Signal(
            signal_type=SignalType.RETENTION_RISK,
            trigger_type=TriggerType.CUSTOMER_LAPSE,
            score=score,
            data={
                "customer_name": customer.get("name"),
                "days_since_visit": days_since,
                "offer_name": offer.get("name") if offer else None,
                "offer_price": offer.get("price") if offer else None,
            },
            rationale=f"Client hasn't visited in {days_since} days" + (f" - {offer.get('name')} available" if offer else ""),
        )


class BridalFollowupRule(BaseRule):
    category = Category.SALON
    trigger_types = [TriggerType.BRIDAL_FOLLOWUP]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        if not customer:
            return None

        wedding_date = customer.get("profile", {}).get("wedding_date")
        if not wedding_date:
            return None

        return Signal(
            signal_type=SignalType.ENGAGEMENT_OPPORTUNITY,
            trigger_type=TriggerType.BRIDAL_FOLLOWUP,
            score=80,
            data={
                "customer_name": customer.get("name"),
                "wedding_date": wedding_date,
            },
            rationale=f"Bridal client wedding approaching: {wedding_date}",
        )


class SeasonalTrendRule(BaseRule):
    category = Category.SALON
    trigger_types = [TriggerType.SEASONAL_TREND]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        trend = trigger.get("payload", {}).get("trend", "")
        season = trigger.get("payload", {}).get("season", "")

        offer = self._find_matching_offer(merchant, [trend, season])

        if not offer:
            return None

        return Signal(
            signal_type=SignalType.REVENUE_OPPORTUNITY,
            trigger_type=TriggerType.SEASONAL_TREND,
            score=70,
            data={
                "trend": trend,
                "season": season,
                "offer_name": offer.get("name"),
                "offer_price": offer.get("price"),
            },
            rationale=f"Seasonal trend '{trend}' for {season} + matching offer",
        )


class StylistAvailabilityRule(BaseRule):
    category = Category.SALON
    trigger_types = [TriggerType.STYLIST_AVAILABILITY]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        stylist = trigger.get("payload", {}).get("stylist_name", "")
        slots = trigger.get("payload", {}).get("available_slots", 0)

        if slots < 3:
            return None

        return Signal(
            signal_type=SignalType.REVENUE_OPPORTUNITY,
            trigger_type=TriggerType.STYLIST_AVAILABILITY,
            score=65,
            data={
                "stylist": stylist,
                "available_slots": slots,
            },
            rationale=f"Stylist {stylist} has {slots} open slots this week",
        )


class PerformanceDipRule(BaseRule):
    category = Category.SALON
    trigger_types = [TriggerType.PERFORMANCE_DIP]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        payload = trigger.get("payload", {})
        decline_pct = payload.get("decline_pct", 0)
        metric = payload.get("metric", "views")

        if decline_pct < 15:
            return None

        offer = self._find_matching_offer(merchant, ["bridal", "spa", "facial", "hair", "package"])

        score = min(85, 50 + decline_pct)
        return Signal(
            signal_type=SignalType.ACQUISITION_DIP,
            trigger_type=TriggerType.PERFORMANCE_DIP,
            score=score,
            data={
                "decline_pct": decline_pct,
                "metric": metric,
                "views_last_week": payload.get("views_last_week", 0),
                "avg_weekly_views": payload.get("avg_weekly_views", 0),
                "offer_name": offer.get("name") if offer else None,
                "offer_price": offer.get("price") if offer else None,
            },
            rationale=f"Salon {metric} dropped {decline_pct}%" + (f" - {offer.get('name')} can help" if offer else ""),
        )


rule_engine.register(Category.SALON, CustomerLapseRule())
rule_engine.register(Category.SALON, BridalFollowupRule())
rule_engine.register(Category.SALON, SeasonalTrendRule())
rule_engine.register(Category.SALON, StylistAvailabilityRule())
rule_engine.register(Category.SALON, PerformanceDipRule())