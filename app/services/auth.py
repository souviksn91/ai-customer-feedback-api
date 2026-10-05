from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt

from app.config import settings

password_hash = PasswordHash.recommended()


# hashes a plain text password 
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# verifies a plain text password against a hashed password
def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


# generates a JWT access token for a given user ID
def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": user_id,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )