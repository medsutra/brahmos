from datetime import datetime
from app.query_models.message import MessageOwner
from app.schemas.base import BaseSchema


class Message(BaseSchema):
    id: str
    message: str
    user_id: str
    owner: MessageOwner
    chat_id: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
