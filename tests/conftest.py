from dotenv import load_dotenv
import pytest


# load test environment variables before importing the application
load_dotenv(".env.test", override=True)

from app.models import APIRequestLog, Feedback, User
from app.database import Base, engine, SessionLocal
from app.dependencies import get_db
from app.main import app



# create all database tables in the test database
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# tell FastAPI to use our test database session
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def clean_database():
    # remove test data before each test
    # this keeps tests independent from one another
    with SessionLocal() as db:
        db.query(APIRequestLog).delete()
        db.query(Feedback).delete()
        db.query(User).delete()
        db.commit()

