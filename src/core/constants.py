from enum import Enum


class Category(str, Enum):
    DENTIST = "dentist"
    SALON = "salon"
    RESTAURANT = "restaurant"
    GYM = "gym"
    PHARMACY = "pharmacy"


class TriggerType(str, Enum):
    SEARCH_SPIKE = "search_spike"
    PERFORMANCE_DIP = "performance_dip"
    CUSTOMER_LAPSE = "customer_lapse"
    REFILL_DUE = "refill_due"
    EVENT = "event"
    RECALL_DUE = "recall_due"
    REVIEW_REQUEST = "review_request"
    OFFER_MATCH = "offer_match"
    BRIDAL_FOLLOWUP = "bridal_followup"
    SEASONAL_TREND = "seasonal_trend"
    STYLIST_AVAILABILITY = "stylist_availability"
    SALES_DIP = "sales_dip"
    NEW_MENU = "new_menu"
    CORPORATE_ENQUIRY = "corporate_enquiry"
    MEMBERSHIP_DIP = "membership_dip"
    TRIAL_CONVERSION = "trial_conversion"
    SEASONAL_SURGE = "seasonal_surge"
    CLASS_WAITLIST = "class_waitlist"
    COMPLIANCE_ALERT = "compliance_alert"
    CHRONIC_CARE = "chronic_care"
    STOCK_ALERT = "stock_alert"
    RESEARCH_DIGEST = "research_digest"
    FESTIVAL = "festival"


class SignalType(str, Enum):
    DEMAND_SPIKE = "demand_spike"
    ACQUISITION_DIP = "acquisition_dip"
    RETENTION_RISK = "retention_risk"
    REVENUE_OPPORTUNITY = "revenue_opportunity"
    OPERATIONAL_ALERT = "operational_alert"
    ENGAGEMENT_OPPORTUNITY = "engagement_opportunity"


class Scope(str, Enum):
    MERCHANT = "merchant"
    CUSTOMER = "customer"


class SendAs(str, Enum):
    VERA = "Vera"
    MERCHANT = "merchant"


DEFAULT_SUPPRESSION_TTL = 86400
MAX_ACTIONS_PER_TICK = 20
CONTEXT_VERSION_KEY = "context:version"
MERCHANT_CONTEXT_PREFIX = "merchant:"
CUSTOMER_CONTEXT_PREFIX = "customer:"
TRIGGER_PREFIX = "trigger:"
CONVERSATION_PREFIX = "conversation:"
SUPPRESSION_PREFIX = "suppression:"
MESSAGE_LOG_PREFIX = "message_log:"