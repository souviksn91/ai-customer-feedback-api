from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict
import uuid
from datetime import datetime

from app.models import Priority, Sentiment



class UserRegister(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)

    # validates that two passwords match
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self

    

class UserLogin(BaseModel):
    email: EmailStr
    password: str



# FEEDBACK SCHEMAS

# client sends the feedback
class FeedbackCreate(BaseModel):
    text: str = Field(min_length=10, max_length=250)


# AI's response to be saved to the DB
class FeedbackAnalysis(BaseModel):
    is_customer_feedback: bool
    summary: str
    sentiment: Sentiment
    category: str
    priority: Priority
    keywords: list[str]


# how our API sends the response to the client
class FeedbackResponse(BaseModel):
    id: uuid.UUID
    text: str
    summary: str
    sentiment: Sentiment
    category: str
    priority: Priority
    keywords: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  