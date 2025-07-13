import datetime
from app.schemas.base import BaseSchema


class Chat(BaseSchema):
    id: str
    title: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True
        from_attributes = True
