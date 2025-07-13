from typing import Optional

from app.query_models.report import ReportStatus
from app.schemas.base import BaseSchema


class Report(BaseSchema):
    id: str
    user_id: str
    status: ReportStatus
    title: Optional[str] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True
