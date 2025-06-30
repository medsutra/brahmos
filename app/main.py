from fastapi import FastAPI

from .routes.report import router as report_router
from .database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI SQLAlchemy SQLite API (MVCS)",
    description="A REST API built with FastAPI, SQLAlchemy, and SQLite, following an MVCS pattern.",
    version="1.0.0",
)

app.include_router(router=report_router)