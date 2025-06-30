import uuid
from sqlalchemy import Column, String, Text
from app.query_models.report import ReportStatus
from ..utils.db.enum_decorator import EnumType
from ..database import Base


class Report(Base):
    __tablename__ = "REPORTS"

    id = Column(
        "ID",
        String(36),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    title = Column("TITLE", String, nullable=True, index=True)
    description = Column("DESCRIPTION", Text, nullable=True)
    status = Column(
        "STATUS", EnumType(ReportStatus), default=ReportStatus.PROCESSING.value
    )
    user_id = Column(
        "USER_ID", String, nullable=False, index=True, foreign_key="USERS.ID"
    )
