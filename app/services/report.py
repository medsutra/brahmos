
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from sqlalchemy.orm import Session
from fastapi import UploadFile
import os

client = genai.Client(api_key=os.environ.get("GOOGLE_GENAI_API_KEY"))

class ReportService:

    @classmethod
    async def upload_report(cls, db: Session, file: UploadFile) -> None:
        """
        Reads the content of an UploadFile and saves it as a BLOB in the database.
        Performs basic validation to ensure the file type is JPEG/JPG.
        """
        file_content = await file.read()

        # Validate file type: only allow JPEG/JPG images
        if file.content_type not in ["image/jpeg", "image/jpg"]:
            raise ValueError("Invalid file type. Only JPEG/JPG images are allowed.")
        
        # Convert bytes to PIL Image
        image = Image.open(BytesIO(file_content))

        model_name = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.0-flash-001")
        response = client.models.generate_content(
            model=model_name,
            contents=["Hey what is this file", image],
        )

        if response.candidates is not None and len(response.candidates) > 0:
            print("Response from Gemini:")
            print(response.text)

        return None