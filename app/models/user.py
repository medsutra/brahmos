from sqlalchemy import Column, Integer, String, Boolean
from ..database import Base


class User(Base):
    __tablename__ = "USERS"

    id = Column("ID", String, primary_key=True, index=True)
    email = Column("EMAIL", String, unique=True, index=True)
    hashed_password = Column("HASHED_PASSWORD", String)
    is_active = Column("IS_ACTIVE", Boolean, default=True)

