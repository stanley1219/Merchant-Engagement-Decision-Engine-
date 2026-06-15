from dataclasses import dataclass

from src.core.constants import Category, SendAs, SignalType


@dataclass(frozen=True)
class MessageTemplate:
    message_template: str
    cta_template: str
    send_as: str


CATEGORY_TEMPLATES: dict[Category, dict[SignalType, MessageTemplate]] = {
    Category.DENTIST: {
        SignalType.DEMAND_SPIKE: MessageTemplate(
            message_template=(
                "High demand for {keyword} in {locality}. "
                "Your practice is getting {searches} searches."
            ),
            cta_template="Boost Your Visibility",
            send_as=SendAs.VERA,
        ),
        SignalType.RETENTION_RISK: MessageTemplate(
            message_template=(
                "{customer_name} hasn't visited in "
                "{days_since_visit} days — send a recall reminder."
            ),
            cta_template="Send Recall Reminder",
            send_as=SendAs.VERA,
        ),
        SignalType.ENGAGEMENT_OPPORTUNITY: MessageTemplate(
            message_template=(
                "Your practice has {review_count} reviews "
                "({review_score}/5.0) — ask for feedback."
            ),
            cta_template="Request Reviews",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "Offer '{offer_name}' at ₹{offer_price} "
                "is live — promote to nearby patients."
            ),
            cta_template="Promote Offer",
            send_as=SendAs.VERA,
        ),
    },
    Category.SALON: {
        SignalType.RETENTION_RISK: MessageTemplate(
            message_template=(
                "{customer_name} hasn't visited in "
                "{days_since_visit} days — re-engage them."
            ),
            cta_template="Re-engage Client",
            send_as=SendAs.VERA,
        ),
        SignalType.ENGAGEMENT_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{customer_name}'s wedding is on "
                "{wedding_date} — offer bridal packages."
            ),
            cta_template="Ping Bridal Client",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{trend} trending for {season}. "
                "Your '{offer_name}' matches perfectly."
            ),
            cta_template="Promote Seasonal Offer",
            send_as=SendAs.VERA,
        ),
    },
    Category.RESTAURANT: {
        SignalType.DEMAND_SPIKE: MessageTemplate(
            message_template=(
                "{event_name} in {locality} driving traffic. "
                "{searches} people searching — run a campaign."
            ),
            cta_template="Run Campaign",
            send_as=SendAs.VERA,
        ),
        SignalType.ACQUISITION_DIP: MessageTemplate(
            message_template=(
                "Sales dipped {dip_percent}% this week "
                "({current} vs {usual} avg). Run a flash offer."
            ),
            cta_template="Create Flash Offer",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "New menu item '{item_name}' added — "
                "notify regulars to drive discovery orders."
            ),
            cta_template="Notify Regulars",
            send_as=SendAs.VERA,
        ),
    },
    Category.GYM: {
        SignalType.ACQUISITION_DIP: MessageTemplate(
            message_template=(
                "Membership signups dropped {dip_percent}% "
                "({new_members} vs {usual_avg} avg). Run a referral."
            ),
            cta_template="Launch Referral Campaign",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{active_trials} active trials at "
                "{conversion_rate}% conversion — send an offer."
            ),
            cta_template="Send Conversion Offer",
            send_as=SendAs.VERA,
        ),
        SignalType.DEMAND_SPIKE: MessageTemplate(
            message_template=(
                "{season} surge incoming "
                "(+{expected_increase}% demand). Get promos ready."
            ),
            cta_template="Prepare Promotions",
            send_as=SendAs.VERA,
        ),
    },
    Category.PHARMACY: {
        SignalType.RETENTION_RISK: MessageTemplate(
            message_template=(
                "{customer_name} is due for a {medication} refill "
                "({days_since_last_fill} days overdue). Remind them."
            ),
            cta_template="Send Refill Reminder",
            send_as=SendAs.VERA,
        ),
        SignalType.OPERATIONAL_ALERT: MessageTemplate(
            message_template=(
                "Compliance alert: {alert_type} "
                "(severity: {severity}). Take action."
            ),
            cta_template="View Compliance Tasks",
            send_as=SendAs.VERA,
        ),
        SignalType.ENGAGEMENT_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{customer_name}'s {condition} adherence "
                "is at {adherence_score}% — send a check-in."
            ),
            cta_template="Send Care Check-in",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "Low stock: {medication} "
                "({current_stock}/{reorder_level} units). Restock."
            ),
            cta_template="Restock Now",
            send_as=SendAs.VERA,
        ),
    },
}


def get_template(
    category: Category,
    signal_type: SignalType,
) -> MessageTemplate | None:
    category_templates = CATEGORY_TEMPLATES.get(category)
    if not category_templates:
        return None
    return category_templates.get(signal_type)
