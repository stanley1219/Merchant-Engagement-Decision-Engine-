from typing import Any

from groq import AsyncGroq

from src.core.config import get_settings
from src.core.exceptions import LLMError
from src.services.llm.prompts import dentists, gyms, pharmacies, restaurants, salons
from src.services.llm.structured_output import LLMComposeOutput

settings = get_settings()

CATEGORY_PROMPTS: dict[str, str] = {
    "dentist": dentists.SYSTEM_PROMPT,
    "salon": salons.SYSTEM_PROMPT,
    "restaurant": restaurants.SYSTEM_PROMPT,
    "gym": gyms.SYSTEM_PROMPT,
    "pharmacy": pharmacies.SYSTEM_PROMPT,
}


def _get_system_prompt(category: str) -> str:
    prompt = CATEGORY_PROMPTS.get(category)
    if not prompt:
        return CATEGORY_PROMPTS.get("pharmacy", pharmacies.SYSTEM_PROMPT)
    return prompt


class GroqClient:
    def __init__(self) -> None:
        self._client: AsyncGroq | None = None

    def _ensure_client(self) -> AsyncGroq:
        if self._client is not None:
            return self._client
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise LLMError("GROQ_API_KEY is not configured")
        self._client = AsyncGroq(api_key=api_key)
        return self._client

    async def get_available_categories(self) -> list[str]:
        return list(CATEGORY_PROMPTS.keys())

    async def compose(
        self,
        category: str,
        message_template: str,
        cta_template: str,
        signal_data: dict[str, Any],
        merchant_data: dict[str, Any] | None = None,
        send_as_default: str = "Vera",
    ) -> LLMComposeOutput:
        client = self._ensure_client()
        system_prompt = _get_system_prompt(category)
        merchant_identity = merchant_data.get("identity", {}) if merchant_data else {}
        merchant_performance = merchant_data.get("performance", {}) if merchant_data else {}
        user_prompt = (
            f"Polish a message for this scenario:\n\n"
            f"Category: {category}\n"
            f"Merchant: {merchant_identity.get('name', 'Unknown')} "
            f"(Owner: {merchant_identity.get('owner_first_name', 'Owner')}, "
            f"Locality: {merchant_identity.get('locality', 'Unknown')})\n"
            f"Merchant Performance: {merchant_performance}\n"
            f"Base Message: {message_template}\n"
            f"Call to Action: {cta_template}\n"
            f"Signal Data: {signal_data}\n"
            f"Default send_as: {send_as_default}\n\n"
            f"Return JSON with: message, cta, send_as, rationale. "
            f"Personalize with merchant name, locality, and performance metrics. "
            f"Keep the message faithful to the intent of the base message."
        )

        try:
            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            if not response.choices or not response.choices[0].message.content:
                raise LLMError("Empty response from Groq")

            content = response.choices[0].message.content
            parsed: LLMComposeOutput = LLMComposeOutput.model_validate_json(content)
            return parsed

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Groq API call failed: {e}") from e


_groq_client: GroqClient | None = None


async def get_llm() -> GroqClient:
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
