from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.logging_config import configure_logging

from .routes.report import router as report_router
from .routes.chat import router as chat_router
from .database import Base, engine

configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MedSutra Backed API",
    description="A REST API for managing medical reports with AI",
    version="0.0.1",
)

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router=report_router)
app.include_router(router=chat_router)
