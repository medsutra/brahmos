
from enum import Enum
from sqlalchemy import Column, Integer, String, Text

from utils.db.enum_decorator import EnumType
from ..database import Base

class ReportStatus(Enum):
    PROCESSING="PROCESSING"
    COMPLETED="COMPLETED"
    FAILED="FAILED"

class Report(Base):
    __tablename__ = "USERS"

    id = Column("ID", Integer, primary_key=True, index=True)
    title = Column("TITLE", String, unique=True, index=True)
    description = Column("DESCRIPTION", Text, nullable=True)
    status = Column("STATUS", EnumType(ReportStatus), default=ReportStatus.PROCESSING.value)
    user_id = Column("USER_ID", String, nullable=False, index=True, foreign_key="USERS.ID")

