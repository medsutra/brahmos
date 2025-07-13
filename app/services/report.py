import asyncio
import json
import re
from typing import List, Optional
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from io import BytesIO
from sqlalchemy.orm import Session
from fastapi import UploadFile
from fastapi.logger import logger
from app.config import settings
from app.schemas.report import Report
from app.query_models.report import ReportStatus
from app.repositories.report import ReportRepository
from app.services.doctor_agent import DoctorAgent
from app.types.report import MedicalReportAnalysis
from .vector_storage import vector_storage_service


class ReportService:

    @classmethod
    def analyze_image_with_ai(
        cls,
        genai_model_name: str,
        image_data: Image.Image,
        report: Report,
        db: Session,
    ) -> Optional[MedicalReportAnalysis]:
        logger.info(
            f"Initiating AI analysis for medical report using model: {genai_model_name}"
        )
        try:
            response = DoctorAgent.analyze_report(image_data=image_data)

            if (
                response.candidates
                and len(response.candidates) > 0
                and response.candidates[0].content
                and response.candidates[0].content.parts
            ):
                raw_gemini_text = response.candidates[0].content.parts[0].text

                if not raw_gemini_text:
                    logger.error(
                        "Gemini AI response is None. No content received for analysis."
                    )
                    ReportRepository.set_report_failed(db=db, report_id=report.id)
                    return None

                logger.info(
                    f"Gemini AI analysis raw response (first 200 chars): {raw_gemini_text[:200]}..."
                )

                json_string_to_parse = raw_gemini_text

                json_match = re.search(
                    r"```json\n(.*)\n```", raw_gemini_text, re.DOTALL
                )
                if json_match:
                    json_string_to_parse = json_match.group(1).strip()
                    logger.info("Extracted JSON from markdown block for parsing.")

                try:
                    ai_analysis = MedicalReportAnalysis.model_validate_json(
                        json_string_to_parse
                    )
                    ai_analysis.user_id = report.user_id
                    ReportRepository.populate_report(
                        db=db,
                        report_id=report.id,
                        title=ai_analysis.title,
                        description=ai_analysis.summary,
                        status=ReportStatus.COMPLETED,
                    )
                    vector_storage_service.embed_content_for_retrieval(
                        report=ai_analysis,
                        title=ai_analysis.title,
                    )
                    logger.info(
                        f"Gemini AI analysis parsed successfully. Title: '{ai_analysis.title}'"
                    )
                    return ai_analysis
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to decode JSON from Gemini response: {e}. Text attempting to parse: '{json_string_to_parse}'",
                        exc_info=True,
                    )
            else:
                logger.warning(
                    "No valid response candidates or content received from Gemini for image analysis."
                )
                ReportRepository.set_report_failed(db=db, report_id=report.id)
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Gemini AI analysis: {e}",
                exc_info=True,
            )
            ReportRepository.set_report_failed(db=db, report_id=report.id)

    @classmethod
    async def get_reports(cls, db: Session, user_id: str) -> List[Report]:
        return ReportRepository.get_reports_by_user_id(db=db, user_id=user_id)

    @classmethod
    async def get_reports_by_title(
        cls, db: Session, title: str, user_id: str
    ) -> List[Report]:
        return ReportRepository.get_reports_by_title(
            title=title, db=db, user_id=user_id
        )

    @classmethod
    async def delete_report(cls, db, report_id):
        return ReportRepository.delete_report(db=db, report_id=report_id)

    @classmethod
    async def upload_report(cls, db: Session, file: UploadFile, user_id: str) -> Report:
        file_content = await file.read()

        image = Image.open(BytesIO(file_content))

        report = ReportRepository.add_report(
            db=db,
            user_id=user_id,
        )

        asyncio.create_task(
            run_in_threadpool(
                cls.analyze_image_with_ai,
                genai_model_name=settings.GOOGLE_GENAI_MODEL,
                image_data=image,
                report=report,
                db=db,
            )
        )

        return report
