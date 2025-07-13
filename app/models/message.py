import uuid
from sqlalchemy import Column, String, Text
from app.query_models.message import MessageOwner
from app.utils.db.enum_decorator import EnumType
from .base import BaseModel


class Message(BaseModel):
    __tablename__ = "MESSAGES"

    id = Column(
        "ID",
        String(36),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    message = Column("MESSAGE", Text, nullable=False)
    user_id = Column(
        "USER_ID", String, nullable=False, index=True, foreign_key="USERS.ID"
    )
    chat_id = Column("CHAT_ID", String, nullable=True)
    owner = Column("OWNER", EnumType(MessageOwner), default=MessageOwner.USER.value)
