from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import User, Priority, Sentiment
from app.schemas import FeedbackAnalysis


client = TestClient(app)


# create a fake FeedbackAnalysis object for testing
def fake_feedback_analysis():
    return FeedbackAnalysis(
        is_customer_feedback=True,
        summary="Customer is unhappy with the checkout process.",
        sentiment=Sentiment.NEGATIVE,
        category="Checkout/Payment Failure",
        priority=Priority.HIGH,
        keywords=["checkout", "payment", "failure"],
    )



# register a user and get the JWT token for authentication
def get_auth_token():
    # register a test user
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "feedback@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    # log in and get the JWT
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "feedback@example.com",
            "password": "password123",
        },
    )

    return response.json()["access_token"]



# create a fake irrelevant FeedbackAnalysis object for testing
def fake_irrelevant_analysis():
    return FeedbackAnalysis(
        is_customer_feedback=False,
        summary="",
        sentiment=Sentiment.NEUTRAL,
        category="",
        priority=Priority.LOW,
        keywords=[],
    )


# test creating a feedback
def test_create_feedback(clean_database, monkeypatch):
    # replace the real OpenAI call with our fake analysis
    # what monkeypatch does?
    # while this test is running, when feedback.py calls analyze_feedback(), 
    # use this fake function instead
    monkeypatch.setattr(
        "app.routers.v1.feedback.analyze_feedback",
        lambda text: fake_feedback_analysis(),
    )

    token = get_auth_token()

    response = client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "The checkout process failed and my payment did not go through.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["sentiment"] == "Negative"
    assert data["priority"] == "High"



# test creating a feedback with too short text
def test_feedback_too_short(clean_database):
    token = get_auth_token()

    response = client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Too short",
        },
    )

    assert response.status_code == 422



# test creating a feedback with too long text
def test_feedback_too_long(clean_database):
    token = get_auth_token()

    response = client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "A" * 201,
        },
    )

    assert response.status_code == 422


# test creating a feedback with irrelevant text
def fake_irrelevant_analysis():
    return FeedbackAnalysis(
        is_customer_feedback=False,
        summary="",
        sentiment=Sentiment.NEUTRAL,
        category="",
        priority=Priority.LOW,
        keywords=[],
    )




# test that irrelevant feedback is rejected
def test_irrelevant_feedback_rejected(clean_database, monkeypatch):
    monkeypatch.setattr(
        "app.routers.v1.feedback.analyze_feedback",
        lambda text: fake_irrelevant_analysis(),
    )

    token = get_auth_token()

    response = client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "This is a completely random sentence for testing.",
        },
    )

    assert response.status_code == 400



# test GET with pagination
def test_get_feedback_with_pagination(clean_database, monkeypatch):
    monkeypatch.setattr(
        "app.routers.v1.feedback.analyze_feedback",
        lambda text: fake_feedback_analysis(),
    )

    token = get_auth_token()

    # create two feedback records
    for text in [
        "The checkout process failed and my payment did not go through.",
        "The support team resolved my problem very quickly.",
    ]:
        response = client.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": text},
        )

        assert response.status_code == 201

    # request the first page with one item per page
    response = client.get(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": 1, "limit": 1},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1



# test GET with filtering by sentiment
def test_filter_feedback_by_sentiment(clean_database, monkeypatch):
    # monkeypatch the analyze_feedback function to return a fake analysis
    monkeypatch.setattr(  
        "app.routers.v1.feedback.analyze_feedback",
        lambda text: fake_feedback_analysis(),
    )

    token = get_auth_token()

    # create two feedback records
    for text in [
        "The checkout process failed and my payment did not go through.",
        "The support team resolved my problem very quickly.",
    ]:
        response = client.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": text},
        )

        assert response.status_code == 201

    # filter by the sentiment returned by our fake AI response
    response = client.get(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        params={"sentiment": "Negative"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert all(item["sentiment"] == "Negative" for item in data)



# test GET with filtering by priority
def test_filter_feedback_by_priority(clean_database, monkeypatch):
    # monkeypatch the analyze_feedback function to return a fake analysis
    monkeypatch.setattr(
        "app.routers.v1.feedback.analyze_feedback",
        lambda text: fake_feedback_analysis(),
    )

    token = get_auth_token()

    # create two feedback records
    for text in [
        "The checkout process failed and my payment did not go through.",
        "The support team resolved my problem very quickly.",
    ]:
        response = client.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": text},
        )

        assert response.status_code == 201

    # filter by the priority returned by our fake AI response
    response = client.get(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        params={"priority": "High"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert all(item["priority"] == "High" for item in data)



# test deleting a feedback
def test_delete_feedback(clean_database, monkeypatch):
    monkeypatch.setattr(
        "app.routers.v1.feedback.analyze_feedback",
        lambda text: fake_feedback_analysis(),
    )

    token = get_auth_token()

    # create a feedback record
    create_response = client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "The checkout process failed and my payment did not go through.",
        },
    )

    assert create_response.status_code == 201

    feedback_id = create_response.json()["id"]

    # delete the feedback
    response = client.delete(
        f"/api/v1/feedback/{feedback_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    # confirm that the feedback no longer exists
    get_response = client.get(
        f"/api/v1/feedback/{feedback_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404




# test that an admin can access the usage endpoint
def test_admin_can_access_usage(clean_database):
    # register a user (as admin)
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    # make the user an admin directly in the test database
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "admin@example.com").first()
        user.is_admin = True
        db.commit()

    # log in
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "password123",
        },
    )

    token = response.json()["access_token"]

    # access the admin endpoint
    response = client.get(
        "/api/v1/admin/usage",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


# test that a normal user cannot access the admin usage endpoint
def test_normal_user_cannot_access_usage(clean_database):
    # register a normal user
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Normal",
            "last_name": "User",
            "email": "normal@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    # log in
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "normal@example.com",
            "password": "password123",
        },
    )

    token = response.json()["access_token"]

    # try to access the admin endpoint
    response = client.get(
        "/api/v1/admin/usage",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403