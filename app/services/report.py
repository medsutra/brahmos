import json
import re
from typing import Optional
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
    async def analyze_image_with_ai(
        cls,
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
        
        Your analysis will serve two purposes:
        1. Provide clear, detailed explanations for the patient/user to read and understand
        2. Create a specialized vector database entry for building a comprehensive medical knowledge base
        
        Extract the key information, findings, and conclusions. Explain everything in detailed yet easy-to-understand language, using medical expertise but making it accessible to patients.
        
        Based on your professional medical analysis, provide:
        1. A concise, descriptive title for the report
        2. A detailed summary of the report's content
        3. A comprehensive analysis of positive and negative findings (patient-friendly)
        4. Suggestions for further diagnosis and medical consultation (patient-friendly)
        5. Immediate actionable recommendations (patient-friendly)
        6. A specialized vector database field containing all medical information optimized for semantic search

        Return the response **strictly as a JSON object** with the following structure:
        ```json
        {
            "title": "Clear, descriptive title of the medical report",
            "summary": "Comprehensive summary explaining the report's content in patient-friendly language with medical context",
            "analysis": "GOOD_FINDINGS: [Explain all normal, healthy, or positive findings in detail, using medical terminology but explaining what each means in simple terms for patient understanding] | BAD_FINDINGS: [Provide detailed explanation of all abnormal, concerning, or negative findings, explaining their clinical significance and potential health implications in clear, understandable language]",
            "further_diagnosis": "LIKELY_CONDITIONS: [Explain potential medical conditions or diagnoses in patient-friendly terms, describing what each condition means and why the current findings suggest them] | RECOMMENDED_TESTS: [Describe specific medical tests, screenings, or examinations in simple terms, explaining what each test measures, how it's performed, and why it's needed] | SPECIALIST_CONSULTATION: [Recommend specific medical specialists, explaining their expertise in simple terms and why consultation is needed] | POTENTIAL_CAUSES: [Explain possible underlying causes, risk factors, and contributing factors in understandable language with practical context]",
            "immediate_actions": "DIETARY_CHANGES: [Provide specific, practical dietary modifications with clear explanations of foods to include/avoid, portion guidance, and easy-to-understand medical reasoning] | SUPPLEMENTS: [Recommend specific vitamins, minerals, or supplements with clear explanations, natural food sources, and simple justification for each recommendation] | LIFESTYLE_MODIFICATIONS: [Give practical exercise recommendations, sleep advice, stress management techniques, and other lifestyle changes with clear explanations of benefits] | MONITORING: [Explain exactly what symptoms, signs, or parameters to watch for, how often to check, and what changes to report to doctors] | EMERGENCY_SIGNS: [List specific warning signs in clear terms, explaining why each is concerning and when to seek immediate medical attention]",
            "vector_data": "MEDICAL_FINDINGS: [Include all specific test results, laboratory values, imaging findings, vital signs, measurements, normal ranges, abnormal values, clinical significance, biomarkers, indicators] | GOOD_FINDINGS: [List all normal healthy positive findings with medical terminology, normal ranges, healthy indicators, optimal values, good prognostic factors] | BAD_FINDINGS: [Include all abnormal concerning negative findings, elevated levels, decreased values, pathological indicators, risk factors, warning signs] | LIKELY_CONDITIONS: [Comprehensive list of potential diagnoses, medical conditions, diseases, disorders, syndromes, pathologies, differential diagnoses, related conditions, comorbidities] | RECOMMENDED_TESTS: [Specific diagnostic tests, laboratory panels, imaging studies, screenings, examinations, monitoring tests, follow-up assessments, specialized procedures] | SPECIALIST_CONSULTATION: [Medical specialists, subspecialists, healthcare providers, expert consultations, referral recommendations, multidisciplinary team] | POTENTIAL_CAUSES: [Underlying causes, risk factors, contributing factors, environmental factors, genetic factors, lifestyle factors, occupational hazards] | DIETARY_CHANGES: [Nutritional interventions, dietary modifications, food recommendations, nutritional therapy, meal planning, macronutrients, micronutrients, supplements, vitamins, minerals] | SUPPLEMENTS: [Vitamin supplementation, mineral supplementation, nutritional supplements, herbal remedies, natural sources, dosage recommendations, therapeutic supplements] | LIFESTYLE_MODIFICATIONS: [Exercise recommendations, physical activity, fitness programs, sleep hygiene, stress management, behavioral changes, habit modifications, wellness strategies] | MONITORING: [Symptom tracking, parameter monitoring, vital signs, laboratory monitoring, follow-up schedules, surveillance protocols, patient self-monitoring] | EMERGENCY_SIGNS: [Warning signs, red flags, urgent symptoms, critical indicators, immediate medical attention, emergency care, hospital admission criteria]"
        }
        ```
        
        **IMPORTANT INSTRUCTIONS:** 
        - Create patient-friendly explanations for all fields except vector_data
        - Use medical expertise but explain complex terms in simple, understandable language for patient reading
        - Be comprehensive and detailed in all patient-facing explanations
        - The vector_data field should contain rich medical terminology, synonyms, related conditions, test names, drug names, and comprehensive medical concepts for optimal semantic search and case matching in the vector database
        - Include specific medical values, ranges, and measurements in the vector_data field
        - Use varied medical terminology and include alternative names for conditions, tests, and treatments in vector_data
        - Do NOT include any additional text, preambles, or explanations outside the JSON object
        - Only provide the raw JSON, optionally wrapped in a markdown code block (```json...```)
        - Use the pipe symbol (|) to separate different categories within each field for easy parsing
        - If insufficient data is available, clearly state what additional information or tests are needed
        """

        try:

            def blocking_ai_call():
                return DoctorAgent.analyze_report(image_data=image_data)

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
            genai_model_name=settings.GOOGLE_GENAI_MODEL,
            image_data=image,
            report=report,
            db=db,
        )

        return report
