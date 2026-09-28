from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Feedback, User
from app.schemas import FeedbackCreate, FeedbackResponse
from app.services.ai import analyze_feedback


router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"],
)

# create feedback endpoint
# endpoint is: POST /feedback
@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(feedback_data: FeedbackCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    # call the AI
    # analyze the feedback using OpenAI
    # analyze_feedback function takes the feedback text as input 
    # and returns a FeedbackAnalysis object (defined in schemas.py)
    analysis = analyze_feedback(feedback_data.text)

    # create a new Feedback (database) object from FeedbackAnalysis and the current user
    feedback = Feedback(
        user_id=current_user.id,
        text=feedback_data.text,
        summary=analysis.summary,
        sentiment=analysis.sentiment,
        category=analysis.category,
        priority=analysis.priority,
        keywords=analysis.keywords,
    )

    # save the feedback to the database
    db.add(feedback)
    db.commit()

    # refresh the feedback object to get the generated values (like id, created_at)
    db.refresh(feedback)  

    # return feedback as response which will be serialized to FeedbackResponse model
    return feedback