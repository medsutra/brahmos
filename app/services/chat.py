from typing import List, Optional
from app.query_models.message import MessageOwner
from app.repositories.chat import ChatRepository
from app.repositories.message import MessageRepository
from app.schemas.message import Message
from sqlalchemy.orm import Session


class ChatService:
    @classmethod
    async def create_message(
        cls,
        db: Session,
        user_id: str,
        message: str,
        owner: MessageOwner,
        chat_id: Optional[str],
    ) -> Message:

        chat_id_for_message = chat_id

        if chat_id_for_message is None:
            created_chat = ChatRepository.create_chat(
                db=db, title=message, user_id=user_id
            )
            chat_id_for_message = created_chat.id

        created_message = MessageRepository.add_message(
            chat_id=chat_id_for_message,
            db=db,
            message=message,
            owner=owner,
            user_id=user_id,
        )

        return created_message

    @classmethod
    async def get_messages(cls, db: Session, chat_id: str) -> List[Message]:
        return MessageRepository.get_messages_by_chat_id(db=db, chat_id=chat_id)

    @classmethod
    async def get_chats(cls, db: Session, user_id: str):
        return ChatRepository.get_chats_by_user_id(user_id=user_id, db=db)
