from fastapi import FastAPI

from app.database import engine
from app.routers.v1 import router as api_router


app = FastAPI(
    title="AI Customer Feedback Intelligence API",
    version="1.0.0",
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "AI Customer Feedback Intelligence API"}

