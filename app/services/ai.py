from openai import OpenAI

from app.config import settings
from app.schemas import FeedbackAnalysis


client = OpenAI(api_key=settings.openai_api_key)


# accepts feedback as string and returns FeedbackAnalysis Pydantic object
def analyze_feedback(text: str) -> FeedbackAnalysis:  

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a customer feedback analysis assistant. "
                    "Analyze the customer's feedback and return a structured analysis."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        
        text_format=FeedbackAnalysis,
    )

    return response.output_parsed