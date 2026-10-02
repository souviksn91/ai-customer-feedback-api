from fastapi import FastAPI
import logging

from app.database import engine
from app.routers.v1 import router as api_router

# configure the application's basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

app = FastAPI(
    title="AI Customer Feedback Intelligence API",
    version="1.0.0",
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "AI Customer Feedback Intelligence API"}

