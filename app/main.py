from fastapi import FastAPI
import logging

from app.routers.v1 import router as api_router

# configure the application's basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

app = FastAPI(
    title="AI Customer Feedback Intelligence API",
    description=(
        "A FastAPI backend that uses AI to analyze customer feedback "
        "and extract sentiment, category, priority, summary, and keywords. "
        "The API includes JWT authentication, feedback management, "
        "filtering, pagination, daily AI usage limits, and admin usage monitoring."
    ),
    version="1.0.0",
)

app.include_router(api_router)


@app.get("/", tags=["General"], summary="Check API status")
def root():
    return {"message": "AI Customer Feedback Intelligence API"}
