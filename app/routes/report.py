from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.report import Report
from app.response.chat import ChatRequest, ChatResponse
from app.services.doctor_agent import DoctorAgent

from ..database import get_db
from ..services.report import ReportService


router = APIRouter(
    prefix="/report",
    responses={404: {"description": "Not found"}},
)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_report(
    uploaded_file: UploadFile = File(..., media_type="image/jpeg"),
    db: Session = Depends(get_db),
):
    """
    Uploads a report file.

    :param file: The file to be uploaded.
    :return: A success message.
    """

    return await ReportService.upload_report(
        db=db,
        file=uploaded_file,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_doctor(request: ChatRequest):
    """
    Handles conversational chat requests with the Doctor Agent,
    with RAG support for previous reports.
    """
    try:
        history_for_agent = []
        if request.chat_history is not None:
            history_for_agent = [msg.model_dump() for msg in request.chat_history]

        response_content = await DoctorAgent.get_chat_response(
            user_id=request.user_id,
            user_message=request.user_message,
            chat_history=history_for_agent,
        )

        return ChatResponse(data=response_content)
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
