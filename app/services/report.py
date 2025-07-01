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
        logger.info(
            f"Initiating AI analysis for medical report using model: {genai_model_name}"
        )

        prompt = """
        You are an experienced medical doctor and consultant. Analyze the following image, which is a medical report, with the expertise and thoroughness of a healthcare professional.
        
        Extract the key information, findings, and conclusions. Explain everything in detailed yet easy-to-understand language, as if you're speaking to a patient who wants to fully understand their health status.
        
        Based on your professional medical analysis, provide:
        1. A concise, descriptive title for the report.
        2. A detailed summary of the report's content.
        3. A comprehensive analysis of positive and negative findings.
        4. Suggestions for further diagnosis and medical consultation.
        5. Immediate actionable recommendations.

        Return the response **strictly as a JSON object** with the following structure:
        ```json
        {
            "title": "Your generated title here",
            "summary": "Your detailed summary here",
            "analysis": "GOOD_FINDINGS: [As a doctor, thoroughly explain all normal, healthy, or positive findings from the report in detail, using medical terminology but explaining what each means in simple terms] | BAD_FINDINGS: [Provide detailed explanation of all abnormal, concerning, or negative findings, explaining their clinical significance and potential health implications in patient-friendly language]",
            "further_diagnosis": "LIKELY_CONDITIONS: [Based on your medical expertise, list potential medical conditions or diagnoses with detailed explanations of each condition and why the current findings suggest them] | RECOMMENDED_TESTS: [As a consulting physician, suggest specific medical tests, screenings, or examinations with detailed explanations of what each test measures and why it's needed] | SPECIALIST_CONSULTATION: [Recommend specific medical specialists with detailed explanations of their expertise and why consultation is needed] | POTENTIAL_CAUSES: [Provide comprehensive analysis of possible underlying causes, risk factors, and contributing factors with medical explanations in understandable terms]",
            "immediate_actions": "DIETARY_CHANGES: [Provide detailed, specific dietary modifications as a doctor would prescribe, including exact foods to include/avoid, portion guidance, and medical reasoning] | SUPPLEMENTS: [Recommend specific vitamins, minerals, or supplements with exact dosages when possible, natural food sources, and medical justification for each recommendation] | LIFESTYLE_MODIFICATIONS: [Give detailed exercise prescriptions, sleep recommendations, stress management techniques, and other lifestyle changes with medical rationale] | MONITORING: [Specify exactly what symptoms, vital signs, or parameters to track, how often, and what changes to watch for] | EMERGENCY_SIGNS: [List specific warning signs that require immediate medical attention, explaining why each is dangerous and when to seek emergency care]"
        }
        ```
        **IMPORTANT:** 
        - You are acting as a medical professional - provide thorough, detailed explanations as a doctor would.
        - Use medical expertise but explain complex terms in patient-friendly language.
        - Be as specific and detailed as possible in all recommendations and explanations.
        - Do NOT include any additional text, preambles, or explanations outside the JSON object.
        - Only provide the raw JSON, optionally wrapped in a markdown code block (```json...```).
        - Use the pipe symbol (|) to separate different categories within each field for easy parsing in vector database.
        - If insufficient data is available for certain recommendations, state "Insufficient data - recommend comprehensive medical evaluation with [specific tests/consultations]."
        - Provide actionable, evidence-based medical advice that a healthcare professional would give.
        """

        try:

            def blocking_ai_call():
                return genai_client.models.generate_content(
                    model=genai_model_name,
                    contents=[prompt, image_data],
                )

            response = await run_in_threadpool(blocking_ai_call)

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
                ReportRepository.set_report_failed(db=db, report_id=report.id)
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Gemini AI analysis: {e}",
                exc_info=True,
            )
            ReportRepository.set_report_failed(db=db, report_id=report.id)

    @classmethod
    async def upload_report(cls, db: Session, file: UploadFile) -> Report:
        file_content = await file.read()

        if file.content_type not in ["image/jpeg", "image/jpg"]:
            raise ValueError("Invalid file type. Only JPEG/JPG images are allowed.")

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

        return report
