from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)


class DocumentStore:
    """
    Retrieve stored document chunks from Qdrant.

    Supports user-level isolation.

    Every normal application request should provide
    a user_id so BM25 never receives another user's
    document chunks.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
    ):
        self.client = QdrantClient(
            host=host,
            port=port,
            timeout=60,
        )

    # =========================================================
    # Get All Chunks
    # =========================================================

    def get_all_chunks(
        self,
        collection_name: str,
        user_id: str | None = None,
    ) -> list[dict]:
        """
        Retrieve document chunks from Qdrant.

        If user_id is supplied, only chunks belonging
        to that user are returned.

        This is used to build the BM25 index.
        """

        if not user_id:
            raise ValueError(
                "user_id is required when retrieving "
                "document chunks."
            )

        query_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(
                        value=user_id
                    ),
                )
            ]
        )

        results = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        points = results[0]

        documents = []

        for point in points:

            payload = (
                point.payload or {}
            )

            # -------------------------------------------------
            # Defensive ownership check
            # -------------------------------------------------

            if payload.get(
                "user_id"
            ) != user_id:

                continue

            # -------------------------------------------------
            # Required metadata
            # -------------------------------------------------

            chunk_id = payload.get(
                "chunk_id"
            )

            document_id = payload.get(
                "document_id"
            )

            filename = payload.get(
                "filename"
            )

            page_number = payload.get(
                "page_number"
            )

            chunk_index = payload.get(
                "chunk_index"
            )

            text = payload.get(
                "text"
            )

            # -------------------------------------------------
            # Skip malformed chunks
            # -------------------------------------------------

            if not chunk_id:
                continue

            if not document_id:
                continue

            if not text:
                continue

            documents.append(
                {
                    "user_id":
                        user_id,

                    "chunk_id":
                        chunk_id,

                    "document_id":
                        document_id,

                    "filename":
                        filename,

                    "page_number":
                        page_number,

                    "chunk_index":
                        chunk_index,

                    "text":
                        text,
                }
            )

        return documents

    # =========================================================
    # Get Document Chunks
    # =========================================================

    def get_document_chunks(
        self,
        collection_name: str,
        document_id: str,
        user_id: str,
    ) -> list[dict]:
        """
        Retrieve chunks belonging to a specific document
        and authenticated user.
        """

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        query_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(
                        value=user_id
                    ),
                ),
                FieldCondition(
                    key="document_id",
                    match=MatchValue(
                        value=document_id
                    ),
                ),
            ]
        )

        results = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        points = results[0]

        documents = []

        for point in points:

            payload = (
                point.payload or {}
            )

            # -------------------------------------------------
            # Defensive ownership check
            # -------------------------------------------------

            if payload.get(
                "user_id"
            ) != user_id:

                continue

            if payload.get(
                "document_id"
            ) != document_id:

                continue

            documents.append(
                {
                    "user_id":
                        user_id,

                    "chunk_id":
                        payload.get(
                            "chunk_id"
                        ),

                    "document_id":
                        payload.get(
                            "document_id"
                        ),

                    "filename":
                        payload.get(
                            "filename"
                        ),

                    "page_number":
                        payload.get(
                            "page_number"
                        ),

                    "chunk_index":
                        payload.get(
                            "chunk_index"
                        ),

                    "text":
                        payload.get(
                            "text"
                        ),
                }
            )

        return documents