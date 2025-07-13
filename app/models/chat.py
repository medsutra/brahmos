import uuid
from sqlalchemy import Column, String
from .base import BaseModel
from app.query_models.chat import ChatStatus
from ..utils.db.enum_decorator import EnumType


class Chat(BaseModel):
    __tablename__ = "CHATS"

    id = Column(
        "ID",
        String(36),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    title = Column("TITLE", String, nullable=True, index=True)
    status = Column("STATUS", EnumType(ChatStatus), default=ChatStatus.ACTIVE.value)
    user_id = Column(
        "USER_ID", String, nullable=False, index=True, foreign_key="USERS.ID"
    )
    report_id = Column("REPORT_ID", String, nullable=True)
