from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.report import ReportService


router = APIRouter(
    prefix="/report",
    responses={404: {"description": "Not found"}},
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_reports(user_id: str, db: Session = Depends(get_db)):
    results = await ReportService.get_reports(db=db, user_id=user_id)
    return {"data": results}


@router.get("/search", status_code=status.HTTP_200_OK)
async def search_reports(q: str = "", user_id: str = "", db: Session = Depends(get_db)):
    results = await ReportService.get_reports_by_title(db=db, title=q, user_id=user_id)
    return {"data": results}


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    result = await ReportService.delete_report(db=db, report_id=report_id)
    return {"data": result}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_report(
    user_id: str,
    uploaded_file: UploadFile = File(..., media_type="image/jpeg"),
    db: Session = Depends(get_db),
):
    """
    Uploads a report file.

    :param file: The file to be uploaded.
    :return: A success message.
    """

    return await ReportService.upload_report(db=db, file=uploaded_file, user_id=user_id)
