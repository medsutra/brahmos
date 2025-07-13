from fastapi import APIRouter, Depends, HTTPException
from app.repositories.chat import ChatRepository
from app.response.chat import ChatRequest, ChatResponse, CreateChatRequest
from app.services.chat import ChatService
from app.services.doctor_agent import DoctorAgent
from sqlalchemy.orm import Session
from app.query_models.message import MessageOwner

from ..database import get_db


router = APIRouter(
    prefix="/chat",
    responses={404: {"description": "Not found"}},
)


@router.post("")
async def chat_with_doctor(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Handles conversational chat requests with the Doctor Agent,
    with RAG support for previous reports.
    """
    try:
        history_for_agent = []
        if request.chat_id is not None:
            messages = await ChatService.get_messages(chat_id=request.chat_id, db=db)
            history_for_agent = [msg.model_dump() for msg in messages]

        message = await ChatService.create_message(
            chat_id=request.chat_id,
            db=db,
            message=request.user_message,
            owner=MessageOwner.USER,
            user_id=request.user_id,
        )

        request.chat_id = message.chat_id

        response_content = await DoctorAgent.get_chat_response(
            user_id=request.user_id,
            user_message=request.user_message,
            chat_history=history_for_agent,
        )

        await ChatService.create_message(
            chat_id=request.chat_id,
            db=db,
            message=response_content,
            owner=MessageOwner.MODEL,
            user_id=request.user_id,
        )

        response = ChatResponse(data=response_content, chat_id=request.chat_id)

        return {"data": response}
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/{chat_id}")
async def get_messages(chat_id: str, db: Session = Depends(get_db)):
    messages = await ChatService.get_messages(chat_id=chat_id, db=db)
    return {"data": messages}


@router.get("")
async def get_chats(user_id: str, db: Session = Depends(get_db)):
    messages = await ChatService.get_chats(user_id=user_id, db=db)
    return {"data": messages}


@router.post("/create")
async def create_chat(request: CreateChatRequest, db: Session = Depends(get_db)):
    created_chat = ChatRepository.create_chat(
        db=db,
        title=request.title,
        user_id=request.user_id,
    )
    return {"data": created_chat}
