from typing import List
from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct, VectorParams, Distance
from app.config import settings
from app.types.report import MedicalReportAnalysis
from .llm_client import ai_client
from google.genai import types
import uuid


class VectorStorageService:

    def __init__(self) -> None:
        self.vector_storage_client = QdrantClient(
            url=settings.VECTOR_STORAGE_URL, api_key=settings.VECTOR_STORAGE_API_KEY
        )
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

        point = PointStruct(
            id=str(uuid.uuid4()),
            payload=report.model_dump(),
            vector=vector,
        )

        self.vector_storage_client.upsert(
            collection_name=settings.COLLECTION_NAME, points=[point]
        )

    async def search_reports(
        self, user_id: str, query: str, limit: int = 5
    ) -> List[MedicalReportAnalysis]:

        # Are my kidneys normal?

        """
        Searches for relevant medical reports for a specific user based on a query.

        Args:
            user_id: The ID of the user whose reports to search.
            query: The user's natural language query (e.g., "my blood test results").
            limit: The maximum number of reports to retrieve.

        Returns:
            A list of MedicalReportAnalysis objects.
        """
        if not query:
            return []

        try:
            embed_result = ai_client.models.embed_content(
                model=settings.GOOGLE_GENAI_EMBEDDING_MODEL,
                contents=query,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                ),
            )
        except Exception as e:
            print(f"Error embedding query: {e}")
            return []

        if not embed_result.embeddings or not embed_result.embeddings[0].values:
            print("Warning: Query embedding result was empty.")
            return []

        query_vector = embed_result.embeddings[0].values

        try:
            search_result = self.vector_storage_client.search(
                collection_name=settings.COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id),
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
                score_threshold=0.5,
            )
        except Exception as e:
            print(f"Error searching Qdrant: {e}")
            return []

        retrieved_reports = []
        for scored_point in search_result:
            if scored_point.payload:
                try:
                    report = MedicalReportAnalysis(**scored_point.payload)
                    retrieved_reports.append(report)
                except Exception as e:
                    print(f"Error parsing retrieved report payload: {e}")

        return retrieved_reports


vector_storage_service = VectorStorageService()
