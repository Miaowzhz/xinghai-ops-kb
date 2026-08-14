from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    message_id: int
    feedback_type: str = Field(pattern='^(like|dislike)$')
    reason: str | None = Field(default=None, max_length=500)


class FeedbackOut(BaseModel):
    id: int
    message_id: int
    feedback_type: str
    reason: str | None
    status: str
