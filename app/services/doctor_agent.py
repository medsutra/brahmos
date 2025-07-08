from typing import Dict, List, Optional
from app.config import settings
from app.types.report import MedicalReportAnalysis
from app.utils.common.return_as_function import returns_a_function_decorator
from .llm_client import ai_client
from .vector_storage import vector_storage_service


class DoctorAgent:

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
            "conclusion": "Generate a one-sentence conclusion that directly states whether the findings are normal, abnormal, or inconclusive. Based on this, provide a clear, one-line directive on the next steps, scaled to the urgency and severity of the findings. For normal results, state that no further action is needed. For moderately abnormal results that can be managed with lifestyle changes, specify this (e.g., 'requires attention to diet and exercise'). For findings suggesting a potentially serious condition, state the need for immediate specialist consultation and further testing. The tone should be clear, reassuring, and directive.",
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

    chat_prompt_template = """
        You are a compassionate, knowledgeable, and professional medical doctor. Your role is to provide helpful, accurate, and easy-to-understand medical information and advice to patients. You should always maintain a reassuring and empathetic tone.

        When responding, keep the following in mind:
        1.  **Be Clear and Simple:** Avoid overly technical jargon. If medical terms are necessary, explain them simply.
        2.  **Be Direct and Concise:** Provide answers efficiently, focusing on the user's specific query.
        3.  **Prioritize Safety:** If a user describes symptoms that could indicate a serious condition (e.g., severe chest pain, sudden paralysis, heavy bleeding), advise them to seek immediate professional medical attention (e.g., consult a doctor, go to an emergency room, call emergency services). **You must explicitly state that you cannot diagnose or prescribe medication.**
        4.  **Maintain Professional Boundaries:** State clearly that you are an AI and cannot provide a substitute for an in-person consultation, diagnosis, or treatment from a licensed healthcare professional. Always encourage users to consult their doctor for personalized medical advice.
        5.  **Contextualize (if history provided):** Refer to previous messages if the chat history is available to maintain continuity.
        6.  **Use Provided Reports:** If relevant previous medical reports are provided below, synthesize the information from these reports to answer the user's question. Highlight key findings, trends, or significant changes across reports in a patient-friendly manner. If no relevant reports are found, state that you do not have previous report information to draw upon for that specific query.

        ---
        Chat History:
        {chat_history}

        ---
        Relevant Previous Medical Reports (for user '{user_id}'):
        {retrieved_reports_context}
        ---

        User's current message: {user_message}

        Your response as a medical doctor:
    """

    @classmethod
    def analyze_report(cls, image_data):
        return ai_client.models.generate_content(
            model=settings.GOOGLE_GENAI_MODEL,
            contents=[cls.prompt, image_data],
        )

    @classmethod
    async def get_chat_response(
        cls,
        user_id: str,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generates a conversational response from the doctor agent,
        optionally augmented with retrieved medical reports.

        Args:
            user_id: The ID of the user for whom to retrieve reports. This is crucial for RAG.
            user_message: The current message from the user.
            chat_history: A list of previous messages in the format [{"role": "user", "content": "..."}] or [{"role": "model", "content": "..."}].
        Returns:
            A string containing the doctor's conversational response.
        """
        formatted_chat_history = ""
        if chat_history:
            for message in chat_history:
                role_display = "User" if message.get("role") == "user" else "Doctor"
                formatted_chat_history += (
                    f"{role_display}: {message.get('content', '')}\n"
                )

        retrieved_reports_context = "No relevant previous reports found for this query."

        retrieved_reports: List[MedicalReportAnalysis] = (
            await vector_storage_service.search_reports(
                user_id=user_id,
                query=user_message,  # Using user_message as the primary query
                limit=5,  # Limit to last 5 relevant reports as per user's request example
            )
        )

        if retrieved_reports:
            print(f"Found {len(retrieved_reports)} relevant reports.")
            # Format retrieved reports into a string for the LLM prompt
            report_strings = []
            for i, report in enumerate(retrieved_reports):
                report_strings.append(
                    f"--- Medical Report {i+1} (Title: {report.title}) ---"
                )
                report_strings.append(f"Summary: {report.summary}")
                report_strings.append(f"Analysis: {report.analysis}")
                report_strings.append(f"Conclusion: {report.conclusion}")
                # You can add more fields from MedicalReportAnalysis here if relevant to the LLM's response
                report_strings.append("------------------------------------------")
            retrieved_reports_context = "\n".join(report_strings)
        else:
            print("No relevant reports retrieved for this user and query.")

        full_prompt = cls.chat_prompt_template.format(
            user_id=(user_id if user_id else "N/A"),
            user_message=user_message,
            chat_history=formatted_chat_history,
            retrieved_reports_context=retrieved_reports_context,
        )

        try:
            response = ai_client.models.generate_content(
                model=settings.GOOGLE_GENAI_MODEL,
                contents=[full_prompt],
            )

            if hasattr(response, "text"):
                return str(response.text)
            elif response.candidates is not None:
                if (
                    len(response.candidates) > 0
                    and response.candidates[0].content is not None
                    and response.candidates[0].content.parts is not None
                ):
                    llm_response_parts = []
                    for part in response.candidates[0].content.parts:
                        if part.text is not None:
                            llm_response_parts.append(part.text)
                    return "".join(llm_response_parts)
            return "I apologize, but I could not generate a coherent response at this moment. Please try again."

        except Exception as e:
            print(f"Error generating chat response from LLM: {e}")
            return "I'm sorry, I'm currently experiencing technical difficulties and cannot provide a response. Please try again later or consult a human medical professional."
