import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID


def generate_suppression_key(
    trigger_type: str,
    merchant_id: str,
    signal_hash: str,
    customer_id: Optional[str] = None,
) -> str:
    parts = [trigger_type, merchant_id, signal_hash]
    if customer_id:
        parts.append(customer_id)
    return "_".join(parts)


def hash_signal(signal_data: Dict[str, Any]) -> str:
    serialized = json.dumps(signal_data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:12]


def sanitize_phone(phone: str) -> str:
    return re.sub(r"[^\d+]", "", phone)


def format_currency(amount: float, currency: str = "₹") -> str:
    if amount >= 100000:
        return f"{currency}{amount/100000:.1f}L"
    if amount >= 1000:
        return f"{currency}{amount/1000:.1f}K"
    return f"{currency}{amount:,.0f}"


def format_percentage(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def calculate_days_since(date_str: str) -> int:
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - dt).days
    except (ValueError, AttributeError):
        return 0


def truncate_text(text: str, max_length: int = 160) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def extract_numbers(text: str) -> List[float]:
    return [float(x) for x in re.findall(r"[\d,]+\.?\d*", text.replace(",", ""))]


def normalize_category(category: str) -> str:
    return category.lower().strip()


def is_valid_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def merge_contexts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    result = base.copy()
    for key, value in update.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = merge_contexts(result[key], value)
        else:
            result[key] = value
    return result


def get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current