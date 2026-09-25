from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine


app = FastAPI(
    title="AI Customer Feedback Intelligence API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "AI Customer Feedback Intelligence API"}


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": result.scalar()}