from pydantic import BaseModel, Field


class LLMComposeOutput(BaseModel):
    message: str = Field(
        description=(
            "The polished message text, max 500 chars,"
            " personalised for the merchant and customer"
        ),
    )
    cta: str = Field(
        description="The call-to-action button text, max 100 chars",
    )
    send_as: str = Field(
        description="Either 'Vera' (AI assistant) or 'merchant' (from merchant's account)",
        pattern="^(Vera|merchant)$",
    )
    rationale: str = Field(
        description="Brief explanation of why this message was chosen, max 200 chars",
    )
