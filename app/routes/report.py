from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.report import ReportService


router = APIRouter(
    prefix="/report",
    responses={404: {"description": "Not found"}},
)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_report(
    uploaded_file: UploadFile = File(..., media_type="image/jpeg"),
    db: Session = Depends(get_db)
):
    """
    Uploads a report file.

    :param file: The file to be uploaded.
    :return: A success message.
    """

    await ReportService.upload_report(
        db=db,
        file=uploaded_file,
    )

    