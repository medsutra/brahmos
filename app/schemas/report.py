from typing import Optional
from pydantic import BaseModel

from app.query_models.report import ReportStatus


class Report(BaseModel):
    id: str
    user_id: str
    status: ReportStatus
    title: Optional[str] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True
