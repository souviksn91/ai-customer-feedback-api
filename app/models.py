import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import DateTime, String, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB



from app.database import Base



# enums to be used in Feedback model
class Sentiment(str, Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    

# User table
class User(Base):

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    feedback: Mapped[list["Feedback"]] = relationship(back_populates="user")
    api_request_logs: Mapped[list["APIRequestLog"]] = relationship(back_populates="user")



# Feedback table
class Feedback(Base):

    __tablename__ = "feedback"

    # why all columns are nullable=False? 
    # because our endpoint performs the AI analysis before creating a DB object
    # so if OpenAI fails, we won't create an incomplete Feedback object in the DB
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[Sentiment] = mapped_column(SQLEnum(Sentiment), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[Priority] = mapped_column(SQLEnum(Priority), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="feedback")




# APIRequestLog table
# logs every request that actually reaches the OpenAI API
class APIRequestLog(Base):

    __tablename__ = "api_request_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_customer_feedback: Mapped[bool] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="api_request_logs")

