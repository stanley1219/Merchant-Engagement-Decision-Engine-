from dataclasses import dataclass
from typing import Any

from src.core.constants import Category, SignalType, TriggerType
from src.rules.engine import Signal


@dataclass(frozen=True)
class RankedSignal:
    signal: Signal
    final_score: float
    tie_breaker: tuple


SIGNAL_TYPE_WEIGHTS: dict[SignalType, float] = {
    SignalType.OPERATIONAL_ALERT: 1.2,
    SignalType.RETENTION_RISK: 1.15,
    SignalType.REVENUE_OPPORTUNITY: 1.1,
    SignalType.DEMAND_SPIKE: 1.05,
    SignalType.ENGAGEMENT_OPPORTUNITY: 1.0,
    SignalType.ACQUISITION_DIP: 0.95,
}

CATEGORY_TRIGGER_WEIGHTS: dict[Category, dict[TriggerType, float]] = {
    Category.DENTIST: {
        TriggerType.SEARCH_SPIKE: 1.1,
        TriggerType.RECALL_DUE: 1.15,
        TriggerType.REVIEW_REQUEST: 1.0,
        TriggerType.OFFER_MATCH: 1.05,
    },
    Category.SALON: {
        TriggerType.CUSTOMER_LAPSE: 1.15,
        TriggerType.BRIDAL_FOLLOWUP: 1.2,
        TriggerType.SEASONAL_TREND: 1.05,
        TriggerType.STYLIST_AVAILABILITY: 1.0,
    },
    Category.RESTAURANT: {
        TriggerType.EVENT: 1.2,
        TriggerType.SALES_DIP: 1.15,
        TriggerType.NEW_MENU: 1.1,
        TriggerType.CORPORATE_ENQUIRY: 1.05,
    },
    Category.GYM: {
        TriggerType.MEMBERSHIP_DIP: 1.15,
        TriggerType.TRIAL_CONVERSION: 1.1,
        TriggerType.SEASONAL_SURGE: 1.15,
        TriggerType.CLASS_WAITLIST: 1.05,
    },
    Category.PHARMACY: {
        TriggerType.REFILL_DUE: 1.2,
        TriggerType.COMPLIANCE_ALERT: 1.25,
        TriggerType.CHRONIC_CARE: 1.1,
        TriggerType.STOCK_ALERT: 1.15,
    },
}


def _calculate_tie_breaker(signal: Signal, merchant: dict[str, Any]) -> tuple:
    merchant_id = merchant.get("identity", {}).get("merchant_id", "")
    return (
        -signal.score,
        signal.signal_type.value,
        signal.trigger_type.value,
        merchant_id,
    )


def rank_signals(
    signals: list[Signal],
    merchant: dict[str, Any],
    category: Category,
) -> list[RankedSignal]:
    if not signals:
        return []

    category_weights = CATEGORY_TRIGGER_WEIGHTS.get(category, {})

    ranked: list[RankedSignal] = []
    for signal in signals:
        signal_type_weight = SIGNAL_TYPE_WEIGHTS.get(signal.signal_type, 1.0)
        trigger_weight = category_weights.get(signal.trigger_type, 1.0)

        final_score = signal.score * signal_type_weight * trigger_weight

        tie_breaker = _calculate_tie_breaker(signal, merchant)

        ranked.append(
            RankedSignal(
                signal=signal,
                final_score=round(final_score, 2),
                tie_breaker=tie_breaker,
            )
        )

    ranked.sort(key=lambda x: (x.tie_breaker[0], x.tie_breaker[1], x.tie_breaker[2]))

    return ranked


def select_best_signal(
    signals: list[Signal],
    merchant: dict[str, Any],
    category: Category,
) -> RankedSignal | None:
    ranked = rank_signals(signals, merchant, category)
    return ranked[0] if ranked else None
