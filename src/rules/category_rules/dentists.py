from typing import Any, Dict, List, Optional

from src.core.constants import Category, SignalType, TriggerType
from src.rules.engine import BaseRule, Signal, rule_engine


class SearchSpikeRule(BaseRule):
    category = Category.DENTIST
    trigger_types = [TriggerType.SEARCH_SPIKE]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        searches = trigger.get("payload", {}).get("searches", 0)
        keyword = trigger.get("payload", {}).get("keyword", "")
        locality = trigger.get("payload", {}).get("locality", "")

        if searches < 50:
            return None

        offer = self._find_matching_offer(merchant, [keyword, "checkup", "cleaning", "dental"])

        if offer:
            score = min(90, 60 + (searches // 10))
            return Signal(
                signal_type=SignalType.DEMAND_SPIKE,
                trigger_type=TriggerType.SEARCH_SPIKE,
                score=score,
                data={
                    "searches": searches,
                    "keyword": keyword,
                    "locality": locality,
                    "offer_name": offer.get("name"),
                    "offer_price": offer.get("price"),
                },
                rationale=f"High local demand ({searches} searches for '{keyword}') + matching active offer",
            )

        score = min(70, 40 + (searches // 10))
        return Signal(
            signal_type=SignalType.DEMAND_SPIKE,
            trigger_type=TriggerType.SEARCH_SPIKE,
            score=score,
            data={
                "searches": searches,
                "keyword": keyword,
                "locality": locality,
            },
            rationale=f"High local demand ({searches} searches for '{keyword}') but no matching offer",
        )


class RecallDueRule(BaseRule):
    category = Category.DENTIST
    trigger_types = [TriggerType.RECALL_DUE]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        if not customer:
            return None

        days_since = customer.get("profile", {}).get("days_since_last_visit", 0)
        if days_since < 180:
            return None

        return Signal(
            signal_type=SignalType.RETENTION_RISK,
            trigger_type=TriggerType.RECALL_DUE,
            score=75,
            data={
                "customer_name": customer.get("name"),
                "days_since_visit": days_since,
            },
            rationale=f"Patient overdue for recall by {days_since} days",
        )


class ReviewRequestRule(BaseRule):
    category = Category.DENTIST
    trigger_types = [TriggerType.REVIEW_REQUEST]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        review_count = merchant.get("performance", {}).get("review_count", 0)
        review_score = merchant.get("performance", {}).get("review_score", 0)

        if review_count < 10:
            score = 65
        elif review_score < 4.0:
            score = 70
        else:
            score = 55

        return Signal(
            signal_type=SignalType.ENGAGEMENT_OPPORTUNITY,
            trigger_type=TriggerType.REVIEW_REQUEST,
            score=score,
            data={
                "review_count": review_count,
                "review_score": review_score,
            },
            rationale=f"Review profile needs boost ({review_count} reviews, {review_score}/5.0)",
        )


class OfferMatchRule(BaseRule):
    category = Category.DENTIST
    trigger_types = [TriggerType.OFFER_MATCH]

    def evaluate(
        self,
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None,
    ) -> Optional[Signal]:
        offer = self._find_matching_offer(merchant, ["checkup", "cleaning", "whitening", "implant"])

        if not offer:
            return None

        return Signal(
            signal_type=SignalType.REVENUE_OPPORTUNITY,
            trigger_type=TriggerType.OFFER_MATCH,
            score=60,
            data={
                "offer_name": offer.get("name"),
                "offer_price": offer.get("price"),
            },
            rationale=f"Active offer available: {offer.get('name')}",
        )


rule_engine.register(Category.DENTIST, SearchSpikeRule())
rule_engine.register(Category.DENTIST, RecallDueRule())
rule_engine.register(Category.DENTIST, ReviewRequestRule())
rule_engine.register(Category.DENTIST, OfferMatchRule())