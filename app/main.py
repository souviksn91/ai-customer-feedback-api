from fastapi import FastAPI

app = FastAPI(
    title="AI Customer Feedback Intelligence API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "AI Customer Feedback Intelligence API"}