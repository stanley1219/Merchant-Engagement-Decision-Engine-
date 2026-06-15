
from src.api.v1.schemas.compose import ComposeOutput
from src.services.composer.decision_engine import DecisionResult
from src.services.llm.client import GroqClient
from typing import Any

class MessageGenerator:
    def __init__(self, llm: GroqClient | None = None) -> None:
        self._llm = llm

    async def generate(
        self,
        decision: DecisionResult,
        category: str,
        use_llm: bool = True,
        merchant: dict[str, Any] | None = None,
    ) -> ComposeOutput:
        if use_llm and self._llm is not None:
            return await self._polish_with_llm(decision, category, merchant)

        return self._build_direct(decision)

    async def _polish_with_llm(
        self,
        decision: DecisionResult,
        category: str,
        merchant: dict[str, Any] | None = None,
    ) -> ComposeOutput:
        llm_output = await self._llm.compose(
            category=category,
            message_template=decision.message_template,
            cta_template=decision.cta_template,
            signal_data=decision.signal.data,
            merchant_data=merchant,
            send_as_default=decision.send_as,
        )

        return ComposeOutput(
            message=llm_output.message,
            cta=llm_output.cta,
            send_as=llm_output.send_as,
            suppression_key=decision.suppression_key,
            rationale=llm_output.rationale,
        )

    def _build_direct(self, decision: DecisionResult) -> ComposeOutput:
        return ComposeOutput(
            message=decision.message_template,
            cta=decision.cta_template,
            send_as=decision.send_as,
            suppression_key=decision.suppression_key,
            rationale=decision.signal.rationale,
        )
