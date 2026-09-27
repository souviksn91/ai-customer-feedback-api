from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models import User
from app.schemas import UserRegister, UserLogin
from app.services.auth import hash_password, verify_password, create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)



# register endpoint
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):

    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    hashed_password = hash_password(user_data.password)

    user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        hashed_password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "user_id": str(user.id),
    }




# login endpoint
@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    
    user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": str(current_user.id),
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
    }

# account delete endpoint
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    current_user.is_active = False

    db.commit()