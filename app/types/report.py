import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MedicalReportAnalysis(BaseModel):
    title: str = Field(..., description="A concise title for the medical report.")
    summary: str = Field(
        ...,
        description="A detailed summary of the medical report's key findings and information.",
    )
    analysis: str = Field(
        ...,
        description="A comprehensive analysis of the medical report, including insights and conclusions drawn from the data.",
    )
    further_diagnosis: str = Field(
        ...,
        description="Recommendations for further diagnosis or tests that may be needed based on the report's findings.",
    )
    immediate_actions: str = Field(
        ...,
        description="Immediate actions or treatments recommended based on the report's findings.",
    )
    vector_data: str = Field(
        ...,
        description="Vector data representation of the medical report, used for similarity search and retrieval.",
    )
    conclusion: str = Field(..., description="Shows a one line conclusion")
    report_date: datetime.datetime = datetime.datetime.now()
    user_id: Optional[str] = None
