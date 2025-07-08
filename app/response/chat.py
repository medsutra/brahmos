from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional


api_router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    user_id: str
    user_message: str
    chat_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    data: str


class AnalyzeReportRequest(BaseModel):
    user_id: str
    report_text: str


class AnalyzeReportResponse(BaseModel):
    analysis_summary: str
