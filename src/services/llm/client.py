from typing import Any

from google import genai
from google.genai import types

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


class GeminiClient:
    def __init__(self) -> None:
        self._client: genai.Client | None = None

    def _ensure_client(self) -> genai.Client:
        if self._client is not None:
            return self._client
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise LLMError("GEMINI_API_KEY is not configured")
        self._client = genai.Client(api_key=api_key)
        return self._client

    async def get_available_categories(self) -> list[str]:
        return list(CATEGORY_PROMPTS.keys())

    async def compose(
        self,
        category: str,
        message_template: str,
        cta_template: str,
        signal_data: dict[str, Any],
        send_as_default: str = "Vera",
    ) -> LLMComposeOutput:
        client = self._ensure_client()
        system_prompt = _get_system_prompt(category)
        user_prompt = (
            f"Polish a message for this scenario:\n\n"
            f"Category: {category}\n"
            f"Base Message: {message_template}\n"
            f"Call to Action: {cta_template}\n"
            f"Context data: {signal_data}\n"
            f"Default send_as: {send_as_default}\n\n"
            f"Return JSON with: message, cta, send_as, rationale. "
            f"Keep the message faithful to the intent of the base message."
        )

        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS,
                    response_mime_type="application/json",
                    response_schema=LLMComposeOutput,
                ),
            )

            if not response.text:
                raise LLMError("Empty response from Gemini")  # noqa: TRY301

            parsed: LLMComposeOutput = response.parsed
            return parsed  # noqa: TRY300

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Gemini API call failed: {e}") from e


_gemini_client: GeminiClient | None = None


async def get_llm() -> GeminiClient:
    global _gemini_client  # noqa: PLW0603
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
