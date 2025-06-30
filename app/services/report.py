import json
import re
from typing import Optional
from fastapi.concurrency import run_in_threadpool
from google import genai
from PIL import Image
from io import BytesIO
from sqlalchemy.orm import Session
from fastapi import UploadFile
from fastapi.logger import logger
from app.config import settings
from app.models.report import Report
from app.query_models.report import ReportStatus
from app.repositories.report import ReportRepository
from app.types.report import MedicalReportAnalysis

client = genai.Client(api_key=settings.GOOGLE_GENAI_API_KEY)


class ReportService:

    @classmethod
    async def analyze_image_with_ai(
        cls,
        genai_client: genai.Client,
        genai_model_name: str,
        image_data: Image.Image,
        report: Report,
        db: Session,
    ) -> Optional[MedicalReportAnalysis]:
        """
        Sends a medical report image to Google Generative AI for analysis.
        Instructs AI to create a summary and title in JSON format via the prompt.
        Parses and validates the JSON response.
        """
        logger.info(
            f"Initiating AI analysis for medical report using model: {genai_model_name}"
        )

        prompt = """
        Analyze the following image, which is a medical report.
        Extract the key information, findings, and conclusions.
        Based on your analysis, provide:
        1. A concise, descriptive title for the report.
        2. A detailed summary of the report's content.

        Return the response **strictly as a JSON object** with the following structure:
        ```json
        {
            "title": "Your generated title here",
            "summary": "Your detailed summary here"
        }
        ```
        **IMPORTANT:** Do NOT include any additional text, preambles, or explanations outside the JSON object.
        Only provide the raw JSON, optionally wrapped in a markdown code block (```json...```).
        """

        try:

            def blocking_ai_call():
                return genai_client.models.generate_content(
                    model=genai_model_name,
                    contents=[{"text": prompt}, image_data],
                )

            response = await run_in_threadpool(blocking_ai_call)

            if (
                response.candidates
                and len(response.candidates) > 0
                and response.candidates[0].content
                and response.candidates[0].content.parts
            ):
                raw_gemini_text = response.candidates[0].content.parts[0].text
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
                    ReportRepository.populate_report(
                        db=db,
                        report_id=report.id,
                        title=ai_analysis.title,
                        description=ai_analysis.summary,
                        status=ReportStatus.COMPLETED,
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
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Gemini AI analysis: {e}",
                exc_info=True,
            )

    @classmethod
    async def upload_report(cls, db: Session, file: UploadFile) -> None:
        """
        Reads the content of an UploadFile and saves it as a BLOB in the database.
        Performs basic validation to ensure the file type is JPEG/JPG.
        """
        file_content = await file.read()

        if file.content_type not in ["image/jpeg", "image/jpg"]:
            raise ValueError("Invalid file type. Only JPEG/JPG images are allowed.")

        logger.info(
            f"Received file for upload: {file.filename}, size: {len(file_content)} bytes"
        )

        image = Image.open(BytesIO(file_content))

        report = ReportRepository.add_report(
            db=db,
            user_id="default_user_id",
        )

        await cls.analyze_image_with_ai(
            genai_client=client,
            genai_model_name=settings.GOOGLE_GENAI_MODEL,
            image_data=image,
            report=report,
            db=db,
        )

        return None
