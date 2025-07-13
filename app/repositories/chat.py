from typing import List

from app.models.chat import Chat
from app.query_models.chat import ChatStatus
from ..schemas.message import Message as MessageSchema
from ..schemas.chat import Chat as ChatSchema
from ..models.message import Message
from sqlalchemy.orm import Session


class ChatRepository:

    @classmethod
    def get_chats_by_user_id(cls, db: Session, user_id):
        reports = db.query(Chat).filter(
            Chat.user_id == user_id, Chat.status == ChatStatus.ACTIVE
        )
        return list(map(lambda report: ChatSchema.model_validate(report), reports))

    @classmethod
    def create_chat(cls, db: Session, user_id, title):
        chat = Chat(user_id=user_id, title=title, status=ChatStatus.ACTIVE)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return ChatSchema.model_validate(chat)
