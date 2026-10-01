from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid
from sqlalchemy import case, func

from app.models import APIRequestLog, User
from app.schemas import AdminUsageResponse
from app.dependencies import get_db, require_admin


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)





@router.get("/usage", response_model=AdminUsageResponse)
def get_admin_usage(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    # get every user and count of their AI requests
    usage_query = (
        db.query(
            User.id,
            User.first_name,
            User.last_name,
            User.email,
            User.created_at,
            User.is_active,
            User.is_admin,
            # count every request made by the user that reached OpenAI
            func.count(APIRequestLog.id).label("total_ai_requests"),
            # count relevant requests
            func.count(case((APIRequestLog.is_customer_feedback.is_(True), 1))).label("relevant_requests"),
            # count irrelevant requests
            func.count(case((APIRequestLog.is_customer_feedback.is_(False), 1))).label("irrelevant_requests"),
        )
        # outerjoin keeps users with 0 requests in the result set
        .outerjoin(
            APIRequestLog,
            APIRequestLog.user_id == User.id,
        )
        # as we used COUNT, we need to group by the user columns to get correct counts
        .group_by(
            User.id,
            User.first_name,
            User.last_name,
            User.email,
            User.created_at,
            User.is_active,
            User.is_admin,
        )
        # order the users by their account creation date (oldest first)
        .order_by(User.created_at)
        .all()
    )

    # converts query results into dictionaries 
    # matching the AdminUserUsage schema 
    # that will be later used in AdminUsageResponse schema
    users = [
        {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "joined_at": user.created_at,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "total_ai_requests": user.total_ai_requests,
            "relevant_requests": user.relevant_requests,
            "irrelevant_requests": user.irrelevant_requests,
        }
        for user in usage_query
    ]

    # return total count of users and the list of users with their usage data
    return {
        "total_accounts": len(users),
        "users": users,
    }