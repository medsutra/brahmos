from sqlalchemy import Column, DateTime, func
from ..database import Base


class BaseModel(Base):
    __abstract__ = True
    __table_args__ = {"extend_existing": True}
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
