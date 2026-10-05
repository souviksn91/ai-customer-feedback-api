from openai import OpenAI
import logging

from app.config import settings
from app.schemas import FeedbackAnalysis


logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.openai_api_key)

# custom exception for AI service errors
class AIServiceError(Exception):
    """Raised when the AI service cannot analyze feedback."""


# accepts feedback as string and returns FeedbackAnalysis Pydantic object
def analyze_feedback(text: str) -> FeedbackAnalysis:
    try:
        response = client.responses.parse(
            model="gpt-5-mini",
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a customer feedback analysis assistant. "
                        "First determine whether the submitted text is genuine customer feedback "
                        "about a product, service, company, purchase, support experience, or customer experience. "
                        "If it is customer feedback, analyze it normally. "
                        "If it is not customer feedback, set is_customer_feedback to false."
                    ),
                },
                {"role": "user", "content": text},
            ],
            text_format=FeedbackAnalysis,  # Pydantic model for structured output
        )

        return response.output_parsed

    except Exception as exc:
        # log technical error for debugging
        logger.exception("AI service failed while analyzing feedback.")

        raise AIServiceError(
            "The AI service could not analyze the feedback."
        ) from exc