from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.constants import Category, SignalType, TriggerType


@dataclass
class Signal:
    signal_type: SignalType
    trigger_type: TriggerType
    score: float
    data: Dict[str, Any]
    rationale: str


class BaseRule(ABC):
    category: Category
    trigger_types: List[TriggerType]

    @abstractmethod
    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        pass

    def _get_merchant_metric(self, merchant: Dict[str, Any], key: str, default: Any = None) -> Any:
        return merchant.get("performance", {}).get(key, default)

    def _get_active_offers(self, merchant: Dict[str, Any]) -> List[Dict[str, Any]]:
        offers = merchant.get("offers", [])
        return [o for o in offers if o.get("is_active", True)]

    def _find_matching_offer(self, merchant: Dict[str, Any], keywords: List[str]) -> Optional[Dict[str, Any]]:
        offers = self._get_active_offers(merchant)
        for offer in offers:
            name = offer.get("name", "").lower()
            desc = offer.get("description", "").lower()
            for kw in keywords:
                if kw.lower() in name or kw.lower() in desc:
                    return offer
        return None


class RuleEngine:
    def __init__(self):
        self._rules: Dict[Category, List[BaseRule]] = {}

    def register(self, category: Category, rule: BaseRule) -> None:
        if category not in self._rules:
            self._rules[category] = []
        self._rules[category].append(rule)

    def get_rules(self, category: Category) -> List[BaseRule]:
        return self._rules.get(category, [])

    def evaluate_all(
        self,
        category: Category,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> List[Signal]:
        signals = []
        for rule in self.get_rules(category):
            if trigger.get("type") in [t.value for t in rule.trigger_types]:
                signal = rule.evaluate(merchant, trigger, customer)
                if signal:
                    signals.append(signal)
        return signals


rule_engine = RuleEngine()