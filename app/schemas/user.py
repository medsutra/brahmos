from pydantic import EmailStr

from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: list = []  # List of Item schemas for relationships (forward reference)

    class Config:
        orm_mode = True  # Enables ORM mode for Pydantic to work with SQLAlchemy models
        from_attributes = True  # Pydantic v2+ equivalent of orm_mode
