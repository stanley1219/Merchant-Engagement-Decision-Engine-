from typing import Any, Dict, Optional

from src.core.constants import Category, SignalType, TriggerType
from src.rules.engine import BaseRule, Signal, rule_engine


class MembershipDipRule(BaseRule):
    category = Category.GYM
    trigger_types = [TriggerType.MEMBERSHIP_DIP]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        new_members = merchant.get("performance", {}).get("new_members_last_week", 0)
        usual_avg = merchant.get("performance", {}).get("usual_weekly_avg", 0)

        if usual_avg == 0 or new_members >= usual_avg * 0.7:
            return None

        dip_percent = round((1 - new_members / usual_avg) * 100)

        return Signal(
            signal_type=SignalType.ACQUISITION_DIP,
            trigger_type=TriggerType.MEMBERSHIP_DIP,
            score=min(85, 55 + dip_percent),
            data={
                "new_members": new_members,
                "usual_avg": usual_avg,
                "dip_percent": dip_percent,
            },
            rationale=f"New members dropped {dip_percent}% ({new_members} vs {usual_avg} avg)",
        )


class TrialConversionRule(BaseRule):
    category = Category.GYM
    trigger_types = [TriggerType.TRIAL_CONVERSION]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        trial_count = trigger.get("payload", {}).get("active_trials", 0)
        conversion_rate = trigger.get("payload", {}).get("conversion_rate", 0)

        if trial_count < 5 or conversion_rate > 30:
            return None

        return Signal(
            signal_type=SignalType.REVENUE_OPPORTUNITY,
            trigger_type=TriggerType.TRIAL_CONVERSION,
            score=70,
            data={
                "active_trials": trial_count,
                "conversion_rate": conversion_rate,
            },
            rationale=f"{trial_count} active trials but only {conversion_rate}% converting",
        )


class SeasonalSurgeRule(BaseRule):
    category = Category.GYM
    trigger_types = [TriggerType.SEASONAL_SURGE]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        season = trigger.get("payload", {}).get("season", "")
        expected_increase = trigger.get("payload", {}).get("expected_increase", 0)

        offer = self._find_matching_offer(merchant, ["new year", "summer", "wedding", "fitness", "transformation"])

        score = min(80, 50 + expected_increase)
        return Signal(
            signal_type=SignalType.DEMAND_SPIKE,
            trigger_type=TriggerType.SEASONAL_SURGE,
            score=score,
            data={
                "season": season,
                "expected_increase": expected_increase,
                "offer_name": offer.get("name") if offer else None,
                "offer_price": offer.get("price") if offer else None,
            },
            rationale=f"{season} surge expected (+{expected_increase}% demand)" + (f" - {offer.get('name')} ready" if offer else ""),
        )


class ClassWaitlistRule(BaseRule):
    category = Category.GYM
    trigger_types = [TriggerType.CLASS_WAITLIST]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        class_name = trigger.get("payload", {}).get("class_name", "")
        waitlist_count = trigger.get("payload", {}).get("waitlist_count", 0)

        if waitlist_count < 5:
            return None

        return Signal(
            signal_type=SignalType.REVENUE_OPPORTUNITY,
            trigger_type=TriggerType.CLASS_WAITLIST,
            score=75,
            data={
                "class_name": class_name,
                "waitlist_count": waitlist_count,
            },
            rationale=f"{waitlist_count} people waitlisted for {class_name} - add session?",
        )


class AttendanceDropRule(BaseRule):
    category = Category.GYM
    trigger_types = [TriggerType.ATTENDANCE_DROP]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        payload = trigger.get("payload", {})
        checkins_this = payload.get("checkins_this_week", 0)
        avg_checkins = payload.get("avg_weekly_checkins", 1)
        decline_pct = payload.get("decline_pct", 0)

        if decline_pct < 10:
            return None

        offer = self._find_matching_offer(merchant, ["referral", "bring a friend", "guest", "trial", "summer"])

        lost_members = avg_checkins - checkins_this
        score = min(85, 55 + decline_pct)
        return Signal(
            signal_type=SignalType.ACQUISITION_DIP,
            trigger_type=TriggerType.ATTENDANCE_DROP,
            score=score,
            data={
                "dip_percent": decline_pct,
                "period": "week",
                "new_members": checkins_this,
                "usual_avg": avg_checkins,
                "lost_members": max(0, lost_members),
                "offer_name": offer.get("name") if offer else None,
                "offer_price": offer.get("price") if offer else None,
            },
            rationale=f"Check-ins dropped {decline_pct}% this week ({checkins_this} vs {avg_checkins} avg)" + (f" - {offer.get('name')} can help" if offer else ""),
        )


rule_engine.register(Category.GYM, MembershipDipRule())
rule_engine.register(Category.GYM, TrialConversionRule())
rule_engine.register(Category.GYM, SeasonalSurgeRule())
rule_engine.register(Category.GYM, ClassWaitlistRule())
rule_engine.register(Category.GYM, AttendanceDropRule())