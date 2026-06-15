import re

from fastapi import APIRouter

from src.api.v1.schemas.reply import ReplyRequest, ReplyResponse
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/reply", response_model=ReplyResponse)
async def handle_reply(body: ReplyRequest) -> ReplyResponse:
    logger.info(
        "Reply received",
        merchant_id=body.merchant_id,
        conversation_id=body.conversation_id,
        turn_number=body.turn_number,
    )

    message = body.message
    lowered = message.lower().strip()

    is_auto_reply = _is_auto_reply(lowered)
    if is_auto_reply:
        return ReplyResponse(action="end")

    is_hostile = _is_hostile(lowered)
    if is_hostile:
        return ReplyResponse(
            action="end",
            body="We understand. Your preferences have been updated and you will not receive further messages.",
        )

    is_commitment = _is_commitment(lowered)
    if is_commitment:
        return ReplyResponse(
            action="send",
            body="Great! I've prepared a draft campaign for your business. Here's what I suggest: a targeted offer to bring in more customers this week. Shall I go ahead and schedule it?",
        )

    intent = _infer_intent(message)

    if intent == "opt_out":
        return ReplyResponse(
            action="end",
            body="You have been opted out of further messages.",
        )

    if intent in ("interested", "yes"):
        return ReplyResponse(
            action="send",
            body="Excellent! We'll notify the merchant about your interest right away. Is there anything specific you'd like to know more about?",
        )

    if intent == "not_interested":
        return ReplyResponse(
            action="end",
            body="Thanks for letting us know. We'll adjust your preferences.",
        )

    if intent == "complaint":
        return ReplyResponse(
            action="send",
            body="We're sorry to hear that. We'll connect you with the merchant to resolve this.",
        )

    return ReplyResponse(
        action="wait",
        wait_seconds=3600,
    )


def _is_auto_reply(text: str) -> bool:
    patterns = [
        r"thank you for contacting",
        r"our team will respond",
        r"we'll get back to you",
        r"your message is important",
        r"this is an automated",
    ]
    return any(re.search(p, text) for p in patterns)


def _is_hostile(text: str) -> bool:
    hostile_words = [
        "stop", "spam", "useless", "leave me alone", "block",
        "never message", "don't text", "unsubscribe",
    ]
    return any(w in text for w in hostile_words)


def _is_commitment(text: str) -> bool:
    commitment_words = [
        "let's do it", "lets do it", "what's next", "whats next",
        "i'm in", "im in", "let's go", "lets go", "ok do it",
        "yes do it", "proceed", "sure go ahead",
    ]
    return any(w in text for w in commitment_words)


def _infer_intent(content: str) -> str:
    lowered = content.lower().strip()

    stop_words = {"stop", "unsubscribe", "opt out", "don't text", "leave me alone", "block"}
    if any(w in lowered for w in stop_words):
        return "opt_out"

    positive_words = {"yes", "interested", "sure", "ok", "tell me more", "let's do it", "book"}
    if any(w in lowered for w in positive_words):
        return "interested"

    negative_words = {"no", "not interested", "don't want", "leave me", "stop bothering"}
    if any(w in lowered for w in negative_words):
        return "not_interested"

    complaint_words = {"complaint", "issue", "problem", "bad", "poor", "unhappy", "angry", "wrong"}
    if any(w in lowered for w in complaint_words):
        return "complaint"

    return "unknown"
