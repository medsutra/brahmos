from fastapi import APIRouter
from ..schemas.base import BaseSchema
from typing import List, Optional


api_router = APIRouter()


class ChatMessage(BaseSchema):
    role: str
    content: str


class ChatRequest(BaseSchema):
    user_id: str
    user_message: str
    chat_id: Optional[str] = None
    chat_history: Optional[List[ChatMessage]] = []


class CreateChatRequest(BaseSchema):
    user_id: str
    title: str


class ChatResponse(BaseSchema):
    data: str
    chat_id: str


class AnalyzeReportRequest(BaseSchema):
    user_id: str
    report_text: str


class AnalyzeReportResponse(BaseSchema):
    analysis_summary: str
