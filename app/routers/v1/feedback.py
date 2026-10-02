import logging
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, check_feedback_daily_limit
from app.models import Feedback, Sentiment, Priority, User, APIRequestLog
from app.schemas import FeedbackCreate, FeedbackResponse
from app.services.ai import analyze_feedback, AIServiceError


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"],
)



# --------------------------------
# --------------------------------
# create feedback endpoint
# endpoint is: POST api/v1/feedback
@router.post(
        "", 
        response_model=FeedbackResponse, 
        status_code=status.HTTP_201_CREATED,
        # limit the number of feedbacks a user can submit per day to 5
        dependencies=[Depends(check_feedback_daily_limit)],  
        # add a response for 400 Bad Request when the text is not a genuine customer feedback
        responses={
            status.HTTP_400_BAD_REQUEST: {
                "description": "The submitted text is not recognized as genuine customer feedback.",
            },
        }
)
def create_feedback(feedback_data: FeedbackCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    # call the AI
    # analyze the feedback using OpenAI
    # analyze_feedback function takes the feedback text as input 
    # and returns a FeedbackAnalysis object (defined in schemas.py)
    # added try-except to handle errors if OpenAI fails to analyze the feedback
    try: 
        analysis = analyze_feedback(feedback_data.text)
    except AIServiceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback analysis service is temporarily unavailable. Please try again later."
        )

    # save the API request log to the APIRequestLog table in the database
    # save whether the text is a genuine customer feedback
    # try: log every successfuk request
    try:
        api_request_log = APIRequestLog(
            user_id=current_user.id,
            request_text=feedback_data.text,
            is_customer_feedback=analysis.is_customer_feedback,  
            )
        
        db.add(api_request_log)
        
        # if the text is not recognized as genuine customer feedback, 
        # # first commit save to APIRequestLog table (IMPORTANT)
        # # then raise an exception
        if not analysis.is_customer_feedback:
            db.commit() 
            # this exception is only for client's information
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The submitted text is not recognized as genuine customer feedback.",
            )
        
        # create a new Feedback (database) object from FeedbackAnalysis and the current user
        # # save the feedback to the Feedback table in the database
        feedback = Feedback(
            user_id=current_user.id,
            text=feedback_data.text,
            summary=analysis.summary,
            sentiment=analysis.sentiment,
            category=analysis.category,
            priority=analysis.priority,
            keywords=analysis.keywords,
        )
        db.add(feedback)
        db.commit()
        
        # refresh the feedback object to get the generated values (like id, created_at)
        db.refresh(feedback)  
        
        # return feedback as response which will be serialized to FeedbackResponse model
        return feedback

    # we do not want our own 400 response (for irrevalent feedback) to become a 500 error, 
    # so we catch it and re-raise it
    except HTTPException:
        raise
    except Exception:
        # if any other exception occurs, rollback the transaction
        db.rollback()
        # log technical error for debugging
        logger.exception("Database error while saving feedback.")
        # and return a 500 Internal Server Error to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while saving the feedback.",
        )




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



