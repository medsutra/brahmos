from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct, VectorParams, Distance
from app.config import settings
from app.types.report import MedicalReportAnalysis
from .llm_client import ai_client
from google.genai import types
import uuid


class VectorStorageService:

    def __init__(self) -> None:
        self.vector_storage_client = QdrantClient(settings.VECTOR_STORAGE_URL)
        try:
            self.vector_storage_client.get_collection(
                collection_name=settings.COLLECTION_NAME
            )
        except Exception:
            self.vector_storage_client.recreate_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.VECTOR_SIZE, distance=Distance.COSINE
                ),
            )

            self.vector_storage_client.create_payload_index(
                collection_name=settings.COLLECTION_NAME,
                field_name="user_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            self.vector_storage_client.create_payload_index(
                collection_name=settings.COLLECTION_NAME,
                field_name="title",
                field_schema=models.PayloadSchemaType.TEXT,
            )
            self.vector_storage_client.create_payload_index(
                collection_name=settings.COLLECTION_NAME,
                field_name="analysis",
                field_schema=models.PayloadSchemaType.TEXT,
            )

    def embed_content_for_retrieval(self, report: MedicalReportAnalysis, title: str):
        result = ai_client.models.embed_content(
            model=settings.GOOGLE_GENAI_EMBEDDING_MODEL,
            contents=report.vector_data,
            config=types.EmbedContentConfig(
                title=title,
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )

        if result.embeddings is None:
            return

        if len(result.embeddings) == 0:
            return

        vector = result.embeddings[0].values

        if vector is None:
            return

        points = PointStruct(
            id=str(uuid.uuid4()),
            payload=report.model_dump(),
            vector=vector,
        )

        self.vector_storage_client.upsert(
            collection_name=settings.COLLECTION_NAME, points=[points]
        )


vector_storage_service = VectorStorageService()
