from fastapi.testclient import TestClient

from app.main import app


# create a test client for our FastAPI application.
client = TestClient(app)


def test_root():
    # automated version of what we do manually in Swagger
    # like sending a GET request to the root endpoint
    response = client.get("/")

    # check if the API returned HTTP 200.
    assert response.status_code == 200

    # check if the response contains the expected JSON.
    assert response.json() == {
        "message": "AI Customer Feedback Intelligence API"
    }