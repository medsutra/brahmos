from pydantic import BaseModel, Field


class MedicalReportAnalysis(BaseModel):
    title: str = Field(..., description="A concise title for the medical report.")
    summary: str = Field(
        ...,
        description="A detailed summary of the medical report's key findings and information.",
    )
