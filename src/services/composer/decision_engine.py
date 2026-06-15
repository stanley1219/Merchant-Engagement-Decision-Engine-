from dataclasses import dataclass
from typing import Any

from src.core.constants import Category
from src.rules.engine import Signal, rule_engine
from src.services.composer.signal_ranker import select_best_signal
from src.services.composer.suppression_engine import SuppressionEngine
from src.services.composer.template_selector import get_template


@dataclass
class DecisionResult:
    signal: Signal
    message_template: str
    cta_template: str
    send_as: str
    suppression_key: str
    is_suppressed: bool


class DecisionEngine:
    def __init__(self, suppression_engine: SuppressionEngine) -> None:
        self._suppression = suppression_engine

    async def decide(
        self,
        category: Category,
        merchant: dict[str, Any],
        trigger: dict[str, Any],
        customer: dict[str, Any] | None = None,
        force: bool = False,
    ) -> DecisionResult | None:
        signals = rule_engine.evaluate_all(category, merchant, trigger, customer)
        if not signals:
            return None

        ranked = select_best_signal(signals, merchant, category)
        if not ranked:
            return None

        signal = ranked.signal
        template = get_template(category, signal.signal_type)
        if not template:
            return None

        merchant_id = merchant.get("identity", {}).get("merchant_id", "unknown")
        customer_id = customer.get("identity", {}).get("customer_id") if customer else None

        message = template.message_template.format(**signal.data)
        cta = template.cta_template.format(**signal.data)

        is_suppressed, suppression_key = await self._suppression.check_and_suppress(
            merchant_id=merchant_id,
            trigger_type=signal.trigger_type.value,
            signal_data=signal.data,
            customer_id=customer_id,
        )

        if is_suppressed and not force:
            return None

        return DecisionResult(
            signal=signal,
            message_template=message,
            cta_template=cta,
            send_as=template.send_as.value,
            suppression_key=suppression_key,
            is_suppressed=is_suppressed,
        )
