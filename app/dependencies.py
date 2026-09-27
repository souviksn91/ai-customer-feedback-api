import jwt
from collections.abc import Generator
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.database import SessionLocal


# dependency to get a database session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()



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