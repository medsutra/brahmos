from typing import List
from ..schemas.message import Message as MessageSchema
from ..models.message import Message
from sqlalchemy.orm import Session


class MessageRepository:

    @classmethod
    def add_message(cls, db: Session, user_id, message, owner, chat_id):
        message = Message(
            user_id=user_id, message=message, owner=owner, chat_id=chat_id
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return MessageSchema.model_validate(message)

    @classmethod
    def get_messages_by_chat_id(cls, db: Session, chat_id) -> List[MessageSchema]:
        messages = (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created_at)
        )
        return list(map(lambda report: MessageSchema.model_validate(report), messages))
