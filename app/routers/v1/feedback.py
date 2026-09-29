import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Feedback, Sentiment, Priority, User
from app.schemas import FeedbackCreate, FeedbackResponse
from app.services.ai import analyze_feedback


router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"],
)



# --------------------------------
# --------------------------------
# create feedback endpoint
# endpoint is: POST api/v1/feedback
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




# --------------------------------
# get the list of feedbacks for the current user
# endpoint is: GET api/v1/feedback
@router.get("", response_model=list[FeedbackResponse])
# filter by sentiment and priority if provided (None means not mandatory)
# add pagination with page and limit query parameters 
# get the current user from the token
def get_feedback(
    sentiment: Sentiment | None = None,  
    priority: Priority | None = None,   
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # get the feedback only for the current user
    query = (db.query(Feedback).filter(Feedback.user_id == current_user.id))

    # filter by sentiment
    if sentiment is not None:
        query = query.filter(Feedback.sentiment == sentiment)

    # filter by priority
    if priority is not None:
        query = query.filter(Feedback.priority == priority)

    # pagination
    offset = (page - 1) * limit

    # order by created_at descending, then apply offset and limit for pagination
    feedback_list = (
        query
        .order_by(Feedback.created_at.desc())  
        .offset(offset)
        .limit(limit)
        .all()
    )

    # return the list of feedbacks
    return feedback_list




# --------------------------------
# get a single feedback of the current user by feedback_id
# endpoint is: GET api/v1/feedback/{feedback_id}
@router.get("/{feedback_id}", response_model=FeedbackResponse)
def get_feedback_by_id(feedback_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    # get the feedback only for the current user
    feedback = (db.query(Feedback).filter(Feedback.id == feedback_id, Feedback.user_id == current_user.id).first())

    # if feedback is None, raise an exception
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # return the feedback with FeedbackResponse model 
    # which will be serialized to JSON
    return feedback





# --------------------------------
# delete a single feedback of the current user by feedback_id
# endpoint is: DELETE api/v1/feedback/{feedback_id}
@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(feedback_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    # get the feedback only for the current user
    feedback = (db.query(Feedback).filter(Feedback.id == feedback_id, Feedback.user_id == current_user.id).first())

    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # delete the feedback from the database
    db.delete(feedback)
    db.commit()



