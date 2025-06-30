from fastapi import FastAPI

from app.logging_config import configure_logging

from .routes.report import router as report_router
from .database import Base, engine

configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MedSutra Backed API",
    description="A REST API for managing medical reports with AI",
    version="0.0.1",
)

app.include_router(router=report_router)
