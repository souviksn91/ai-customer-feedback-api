import jwt
from collections.abc import Generator
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.config import settings
from app.models import APIRequestLog, User
from app.database import SessionLocal


# --------------------------------
# dependency to get a database session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()



# --------------------------------
# this will be used to extract the token from the Authorization header
security = HTTPBearer()

# dependency to get the current user from the token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:

    # extract the token from the credentials
    token = credentials.credentials  

    # decode the token 
    try:  
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # get the user_id from the payload
    user_id = payload.get("sub")

    # if user_id is None, raise an exception
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # get the user from the database using the user_id
    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    # if user is None, raise an exception
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # if user is inactive, raise an exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # return the user
    return user



# --------------------------------
# dependency to check if the current user has reached daily limit
def check_feedback_daily_limit(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:

    # if the user is an admin, skip the limit check
    if current_user.is_admin:
        return

    # get the current date in IST timezone
    kolkata_now = datetime.now(ZoneInfo("Asia/Kolkata"))
    kolkata_today_start = kolkata_now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    # converts the IST start of the day to UTC for comparison with the created_at column in the database
    today_start_utc = kolkata_today_start.astimezone(timezone.utc)

    # count the number of feedbacks submitted by the user today
    request_count = (
        db.query(APIRequestLog)
        .filter(
            APIRequestLog.user_id == current_user.id,
            APIRequestLog.created_at >= today_start_utc,  
        )
        .count()
    )

    # if the user has submitted 5 or more feedbacks today, raise an exception
    if request_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily feedback submission limit reached. Please try again tomorrow.",
        )



# --------------------------------
# dependency to check if the current user is an admin
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return current_user