from typing import Any

from src.core.constants import Category, SignalType, TriggerType
from src.rules.engine import BaseRule, Signal, rule_engine

REFILL_MIN_DAYS = 7
ADHERENCE_HIGH_THRESHOLD = 90
ADHERENCE_LOW_THRESHOLD = 70
CONSULTATION_RECENT_DAYS = 90
CONSULTATION_OVERDUE_DAYS = 180


class RefillDueRule(BaseRule):
    category = Category.PHARMACY
    trigger_types = [TriggerType.REFILL_DUE]

    def evaluate(
        self,
        merchant: dict[str, Any],
        trigger: dict[str, Any],
        customer: dict[str, Any] | None = None,
    ) -> Signal | None:
        if not customer:
            return None

        medication = trigger.get("payload", {}).get("medication", "")
        days_since = trigger.get("payload", {}).get("days_since_last_fill", 0)
        refill_count = trigger.get("payload", {}).get("refills_remaining", 0)

        if days_since < REFILL_MIN_DAYS:
            return None

        score = min(85, 55 + (days_since // 3))
        if refill_count == 0:
            score = min(95, score + 15)

        return Signal(
            signal_type=SignalType.RETENTION_RISK,
            trigger_type=TriggerType.REFILL_DUE,
            score=score,
            data={
                "customer_name": customer.get("name"),
                "medication": medication,
                "days_since_last_fill": days_since,
                "refills_remaining": refill_count,
            },
            rationale=(
                f"Patient due for refill: {medication} "
                f"({days_since} days since last fill, {refill_count} refills left)"
            ),
        )


class ComplianceAlertRule(BaseRule):
    category = Category.PHARMACY
    trigger_types = [TriggerType.COMPLIANCE_ALERT]

    def evaluate(
        self,
        merchant: dict[str, Any],
        trigger: dict[str, Any],
        customer: dict[str, Any] | None = None,
    ) -> Signal | None:
        alert_type = trigger.get("payload", {}).get("alert_type", "")
        severity = trigger.get("payload", {}).get("severity", "medium")
        deadline = trigger.get("payload", {}).get("deadline", "")

        if not alert_type:
            return None

        severity_scores = {"low": 40, "medium": 65, "high": 85, "critical": 95}
        score = severity_scores.get(severity.lower(), 50)

        return Signal(
            signal_type=SignalType.OPERATIONAL_ALERT,
            trigger_type=TriggerType.COMPLIANCE_ALERT,
            score=score,
            data={
                "alert_type": alert_type,
                "severity": severity,
                "deadline": deadline,
            },
            rationale=(
                f"Compliance alert: {alert_type} ({severity})"
                + (f" - deadline: {deadline}" if deadline else "")
            ),
        )


class ChronicCareRule(BaseRule):
    category = Category.PHARMACY
    trigger_types = [TriggerType.CHRONIC_CARE]

    def evaluate(
        self,
        merchant: dict[str, Any],
        trigger: dict[str, Any],
        customer: dict[str, Any] | None = None,
    ) -> Signal | None:
        if not customer:
            return None

        condition = trigger.get("payload", {}).get("condition", "")
        last_consultation = trigger.get("payload", {}).get("days_since_consultation", 0)
        adherence_score = trigger.get("payload", {}).get("adherence_score", 100)

        if not condition:
            return None

        if (adherence_score >= ADHERENCE_HIGH_THRESHOLD
                and last_consultation < CONSULTATION_RECENT_DAYS):
            return None

        score = 50
        if adherence_score < ADHERENCE_LOW_THRESHOLD:
            score += 25
        if last_consultation > CONSULTATION_OVERDUE_DAYS:
            score += 20
        elif last_consultation > CONSULTATION_RECENT_DAYS:
            score += 10

        return Signal(
            signal_type=SignalType.ENGAGEMENT_OPPORTUNITY,
            trigger_type=TriggerType.CHRONIC_CARE,
            score=min(85, score),
            data={
                "customer_name": customer.get("name"),
                "condition": condition,
                "days_since_consultation": last_consultation,
                "adherence_score": adherence_score,
            },
            rationale=(
                f"Chronic care follow-up for {condition} "
                f"(adherence: {adherence_score}%, last consult: {last_consultation}d ago)"
            ),
        )


class StockAlertRule(BaseRule):
    category = Category.PHARMACY
    trigger_types = [TriggerType.STOCK_ALERT]

    def evaluate(
        self,
        merchant: dict[str, Any],
        trigger: dict[str, Any],
        customer: dict[str, Any] | None = None,
    ) -> Signal | None:
        medication = trigger.get("payload", {}).get("medication", "")
        current_stock = trigger.get("payload", {}).get("current_stock", 0)
        reorder_level = trigger.get("payload", {}).get("reorder_level", 10)
        demand_forecast = trigger.get("payload", {}).get("demand_forecast", 0)

        if not medication:
            return None

        if current_stock > reorder_level:
            return None

        stockout_risk = max(0, 1 - (current_stock / max(reorder_level, 1)))
        score = min(90, 50 + int(stockout_risk * 40))

        return Signal(
            signal_type=SignalType.REVENUE_OPPORTUNITY,
            trigger_type=TriggerType.STOCK_ALERT,
            score=score,
            data={
                "medication": medication,
                "current_stock": current_stock,
                "reorder_level": reorder_level,
                "demand_forecast": demand_forecast,
            },
            rationale=(
                f"Low stock alert: {medication} "
                f"({current_stock}/{reorder_level} units, forecast: {demand_forecast}/week)"
            ),
        )


rule_engine.register(Category.PHARMACY, RefillDueRule())
rule_engine.register(Category.PHARMACY, ComplianceAlertRule())
rule_engine.register(Category.PHARMACY, ChronicCareRule())
rule_engine.register(Category.PHARMACY, StockAlertRule())

