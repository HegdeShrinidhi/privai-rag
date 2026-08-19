import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)


class VectorStore:
    """
    Qdrant vector database service.

    Supports:

    - Local Docker Qdrant for development
    - Qdrant Cloud for production
    - User-level document isolation
    - Document-level filtering
    - Vector search
    - Document discovery
    - Document existence checks
    - Document deletion
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
    ):
        # =====================================================
        # Qdrant configuration
        # =====================================================

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        # =====================================================
        # Qdrant Cloud
        # =====================================================

        if qdrant_url:

            print(
                "Connecting to Qdrant Cloud..."
            )

            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=60,
            )

            print(
                "Qdrant Cloud client initialized."
            )

        # =====================================================
        # Local Docker Qdrant
        # =====================================================

        else:

            print(
                f"Connecting to local Qdrant "
                f"at {host}:{port}..."
            )

            self.client = QdrantClient(
                host=host,
                port=port,
                timeout=60,
            )

            print(
                "Local Qdrant client initialized."
            )

    # =========================================================
    # Create Payload Indexes
    # =========================================================

    def create_payload_indexes(
        self,
        collection_name: str,
    ):
        """
        Create payload indexes required for filtering.

        Required indexes:

        - user_id
        - document_id
        """

        indexes = [
            ("user_id", "user_id"),
            ("document_id", "document_id"),
        ]

        for field_name, label in indexes:

            try:

                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=PayloadSchemaType.KEYWORD,
                )

                print(
                    f"Payload index created: {label}"
                )

            except Exception as exc:

                # Qdrant returns an error if the index
                # already exists. That is safe to ignore.
                print(
                    f"{label} index check: {exc}"
                )

    # =========================================================
    # Collection
    # =========================================================

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
    ):
        """
        Create the collection if it does not exist.

        If the collection already exists, make sure the
        required payload indexes are present.
        """

        collections = self.client.get_collections()

        existing_collections = [
            collection.name
            for collection in collections.collections
        ]

        if collection_name in existing_collections:

            print(
                f"Collection already exists: "
                f"{collection_name}"
            )

            self.create_payload_indexes(
                collection_name
            )

            return

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

        print(
            f"Created Qdrant collection: "
            f"{collection_name}"
        )

        self.create_payload_indexes(
            collection_name
        )

    # =========================================================
    # Collection Exists
    # =========================================================

    def collection_exists(
        self,
        collection_name: str,
    ) -> bool:
        """
        Check whether a collection exists.
        """

        collections = self.client.get_collections()

        return any(
            collection.name == collection_name
            for collection in collections.collections
        )

    # =========================================================
    # Upsert Chunks
    # =========================================================

    def upsert_chunks(
        self,
        collection_name: str,
        chunks: list[dict],
        embeddings: list[list[float]],
        user_id: str,
    ):
        """
        Store document chunks and embeddings.

        Qdrant point IDs must be UUIDs or unsigned integers.

        The application's original chunk_id remains in
        the payload.
        """

        if len(chunks) != len(embeddings):

            raise ValueError(
                "Number of chunks and embeddings "
                "must match."
            )

        if not user_id:

            raise ValueError(
                "user_id is required when "
                "storing document chunks."
            )

        # Ensure indexes exist before storing data.

        self.create_payload_indexes(
            collection_name
        )

        points = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):

            payload = {
                "user_id": user_id,

                "chunk_id": chunk[
                    "chunk_id"
                ],

                "document_id": chunk[
                    "document_id"
                ],

                "filename": chunk[
                    "filename"
                ],

                "page_number": chunk[
                    "page_number"
                ],

                "chunk_index": chunk[
                    "chunk_index"
                ],

                "text": chunk[
                    "text"
                ],
            }

            # -------------------------------------------------
            # Deterministic UUID
            # -------------------------------------------------
            #
            # Same user + same chunk_id => same point ID.
            #
            # This makes repeated indexing idempotent.
            #

            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{user_id}:{chunk['chunk_id']}",
                )
            )

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )

            points.append(point)

        if not points:

            print(
                "No points to store."
            )

            return

        self.client.upsert(
            collection_name=collection_name,
            points=points,
        )

        print(
            f"Stored {len(points)} chunks "
            f"for user {user_id}."
        )

    # =========================================================
    # Vector Search
    # =========================================================

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        user_id: str | None = None,
        document_id: str | None = None,
    ):
        """
        Perform semantic vector search.

        Optional filters:

        - user_id
        - document_id
        """

        # Make sure the collection has required indexes.

        self.create_payload_indexes(
            collection_name
        )

        conditions = []

        if user_id:

            conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(
                        value=user_id
                    ),
                )
            )

        if document_id:

            conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(
                        value=document_id
                    ),
                )
            )

        query_filter = None

        if conditions:

            query_filter = Filter(
                must=conditions
            )

        # =====================================================
        # Qdrant Client 1.19+
        #
        # query_points() is the current API.
        # =====================================================

        results = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        # =====================================================
        # Defensive ownership verification
        # =====================================================

        secure_results = []

        for point in results.points:

            payload = (
                point.payload or {}
            )

            if (
                user_id is not None
                and payload.get(
                    "user_id"
                ) != user_id
            ):

                continue

            if (
                document_id is not None
                and payload.get(
                    "document_id"
                ) != document_id
            ):

                continue

            secure_results.append(
                point
            )

        return secure_results

    # =========================================================
    # Get All Points
    # =========================================================

    def get_all_points(
        self,
        collection_name: str,
        user_id: str | None = None,
    ) -> list:
        """
        Retrieve all indexed points.

        If user_id is provided, only that user's chunks
        are returned.
        """

        self.create_payload_indexes(
            collection_name
        )

        query_filter = None

        if user_id:

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

        all_points = []

        offset = None

        while True:

            points, next_offset = (
                self.client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    scroll_filter=query_filter,
                    with_payload=True,
                    with_vectors=False,
                )
            )

            # Defensive ownership filtering.

            for point in points:

                payload = (
                    point.payload or {}
                )

                if (
                    user_id is not None
                    and payload.get(
                        "user_id"
                    ) != user_id
                ):
                    continue

                all_points.append(
                    point
                )

            if next_offset is None:
                break

            offset = next_offset

        return all_points

    # =========================================================
    # Document Exists
    # =========================================================

    def document_exists(
        self,
        collection_name: str,
        document_id: str,
        user_id: str | None = None,
    ) -> bool:
        """
        Check whether a document exists.

        If user_id is provided, the document must belong
        to that user.
        """

        self.create_payload_indexes(
            collection_name
        )

        conditions = [
            FieldCondition(
                key="document_id",
                match=MatchValue(
                    value=document_id
                ),
            )
        ]

        if user_id:

            conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(
                        value=user_id
                    ),
                )
            )

        query_filter = Filter(
            must=conditions
        )

        points, _ = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=1,
            with_payload=False,
            with_vectors=False,
        )

        return len(points) > 0

    # =========================================================
    # Delete Document
    # =========================================================

    def delete_document(
        self,
        collection_name: str,
        document_id: str,
        user_id: str,
    ) -> int:
        """
        Delete all chunks belonging to a document.

        The document must belong to the specified user.
        """

        if not user_id:

            raise ValueError(
                "user_id is required when "
                "deleting a document."
            )

        self.create_payload_indexes(
            collection_name
        )

        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(
                        value=document_id
                    ),
                ),
                FieldCondition(
                    key="user_id",
                    match=MatchValue(
                        value=user_id
                    ),
                ),
            ]
        )

        all_point_ids = []

        offset = None

        while True:

            points, next_offset = (
                self.client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    scroll_filter=query_filter,
                    with_payload=False,
                    with_vectors=False,
                )
            )

            all_point_ids.extend(
                point.id
                for point in points
            )

            if next_offset is None:
                break

            offset = next_offset

        if not all_point_ids:

            print(
                f"No chunks found for document "
                f"{document_id}."
            )

            return 0

        self.client.delete(
            collection_name=collection_name,
            points_selector=all_point_ids,
        )

        print(
            f"Deleted {len(all_point_ids)} chunks "
            f"for document {document_id}."
        )

        return len(all_point_ids)