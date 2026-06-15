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
                "Hi {owner_first_name}, high demand for {keyword} in {locality} — "
                "{name} is getting {searches} searches this week. "
                "This surge won't last. Capture this traffic today."
            ),
            cta_template="Boost {name}'s Visibility Today",
            send_as=SendAs.VERA,
        ),
        SignalType.RETENTION_RISK: MessageTemplate(
            message_template=(
                "{customer_name} hasn't visited {name} in "
                "{days_since_visit} days — send a recall reminder now."
            ),
            cta_template="Send Recall Reminder Now",
            send_as=SendAs.VERA,
        ),
        SignalType.ENGAGEMENT_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{name} has {review_count} reviews "
                "({review_score}/5.0) on magicpin — ask {customer_name} for feedback today."
            ),
            cta_template="Request Review Now for {name}",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "Offer '{offer_name}' at ₹{offer_price} "
                "is live at {name}, {locality} — promote to nearby patients now."
            ),
            cta_template="Promote {name}'s Offer Now",
            send_as=SendAs.VERA,
        ),
    },
    Category.SALON: {
        SignalType.RETENTION_RISK: MessageTemplate(
            message_template=(
                "{customer_name} hasn't visited {name} in "
                "{days_since_visit} days — re-engage them today."
            ),
            cta_template="Re-engage Client Now for {name}",
            send_as=SendAs.VERA,
        ),
        SignalType.ENGAGEMENT_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{customer_name}'s wedding is on {wedding_date} — "
                "offer bridal packages at {name}, {locality} today."
            ),
            cta_template="Ping Bridal Client Now for {name}",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{trend} trending for {season}. "
                "{name}'s '{offer_name}' matches perfectly — promote today."
            ),
            cta_template="Promote {name}'s Seasonal Offer Now",
            send_as=SendAs.VERA,
        ),
        SignalType.ACQUISITION_DIP: MessageTemplate(
            message_template=(
                "{owner_first_name}, {name} in {locality} — {metric} crashed {decline_pct}% "
                "({views_last_week} vs {avg_weekly_views} avg). Clients are leaving. "
                "Launch an irresistible promo THIS WEEK."
            ),
            cta_template="Launch Promo for {name} NOW",
            send_as=SendAs.VERA,
        ),
    },
    Category.RESTAURANT: {
        SignalType.DEMAND_SPIKE: MessageTemplate(
            message_template=(
                "{event_name} in {locality} driving traffic — "
                "{name} is getting {searches} searches. Run a campaign."
            ),
            cta_template="Run Campaign for {name}",
            send_as=SendAs.VERA,
        ),
        SignalType.ACQUISITION_DIP: MessageTemplate(
            message_template=(
                "{owner_first_name}, {name} in {locality} — orders PLUMMETED {dip_percent}% "
                "({current} vs {usual} avg). Losing ~₹{daily_loss}/day. "
                "Launch a flash combo THIS EVENING."
            ),
            cta_template="Launch Flash Combo for {name} NOW",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "New menu item '{item_name}' added at {name}, {locality} — "
                "notify regulars to drive discovery orders today."
            ),
            cta_template="Notify {name}'s Regulars Now",
            send_as=SendAs.VERA,
        ),
    },
    Category.GYM: {
        SignalType.ACQUISITION_DIP: MessageTemplate(
            message_template=(
                "{owner_first_name}, {name} — check-ins COLLAPSED {dip_percent}% this week "
                "({new_members} vs {usual_avg} avg). Losing {lost_members} members/week. "
                "Launch a referral drive THIS EVENING."
            ),
            cta_template="Launch Referral for {name} NOW",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{name} has {active_trials} active trials at "
                "{conversion_rate}% conversion — send a conversion offer today."
            ),
            cta_template="Send Offer Now to {name}'s Trials",
            send_as=SendAs.VERA,
        ),
        SignalType.DEMAND_SPIKE: MessageTemplate(
            message_template=(
                "{season} surge incoming at {name}, {locality} "
                "(+{expected_increase}% demand). Get promos ready today."
            ),
            cta_template="Prepare {name}'s Promotions Now",
            send_as=SendAs.VERA,
        ),
    },
    Category.PHARMACY: {
        SignalType.RETENTION_RISK: MessageTemplate(
            message_template=(
                "{customer_name} is due for a {medication} refill "
                "({days_since_last_fill} days overdue) — {name}, {locality} can help today."
            ),
            cta_template="Send Refill Reminder Now from {name}",
            send_as=SendAs.VERA,
        ),
        SignalType.OPERATIONAL_ALERT: MessageTemplate(
            message_template=(
                "{owner_first_name}, compliance alert at {name}: {alert_type} "
                "(severity: {severity}). Take action immediately."
            ),
            cta_template="View {name}'s Compliance Tasks Now",
            send_as=SendAs.VERA,
        ),
        SignalType.ENGAGEMENT_OPPORTUNITY: MessageTemplate(
            message_template=(
                "{customer_name}'s {condition} adherence "
                "is at {adherence_score}% — {name} sends a check-in today."
            ),
            cta_template="Send Check-in Now from {name}",
            send_as=SendAs.VERA,
        ),
        SignalType.REVENUE_OPPORTUNITY: MessageTemplate(
            message_template=(
                "CRITICAL: {name}, {locality} — {medications} stock critical "
                "(restock_urgency: {restock_urgency}). Patients WILL go elsewhere. "
                "Place emergency order TODAY."
            ),
            cta_template="Emergency Restock for {name} NOW",
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
