import google.generativeai as gemini_client
from google import genai
from app.config import settings

ai_client = genai.Client(api_key=settings.GOOGLE_GENAI_API_KEY)
