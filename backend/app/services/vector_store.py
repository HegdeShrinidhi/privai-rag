from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)


class VectorStore:
    """
    Qdrant vector database service.

    Responsibilities:

    - Create collections
    - Store document chunks
    - Store user ownership
    - Search vectors
    - Filter by user_id
    - Filter by document_id
    - Retrieve all indexed points
    - Check whether a document exists
    - Delete a document
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
    # Collection
    # =========================================================

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
    ):
        """
        Create Qdrant collection if it does not already exist.
        """

        collections = self.client.get_collections()

        existing_collections = [
            collection.name
            for collection in collections.collections
        ]

        if collection_name not in existing_collections:

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

        else:

            print(
                f"Collection already exists: "
                f"{collection_name}"
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

        Every chunk is associated with a user_id.
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

        points = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):

            point = PointStruct(
                id=str(uuid4()),

                vector=embedding,

                payload={
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
                },
            )

            points.append(point)

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

        Search can be restricted by:

        - user_id
        - document_id

        If document_id is supplied, user_id should also
        be supplied to guarantee ownership isolation.
        """

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

        results = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return results.points

    # =========================================================
    # Get All Points
    # =========================================================

    def get_all_points(
        self,
        collection_name: str,
        user_id: str | None = None,
    ) -> list:
        """
        Retrieve points from Qdrant.

        If user_id is provided, only that user's
        chunks are returned.
        """

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

            all_points.extend(points)

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

        Returns the number of deleted chunks.
        """

        if not user_id:
            raise ValueError(
                "user_id is required when "
                "deleting a document."
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

        points, _ = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=10000,
            with_payload=False,
            with_vectors=False,
        )

        if not points:
            return 0

        point_ids = [
            point.id
            for point in points
        ]

        self.client.delete(
            collection_name=collection_name,
            points_selector=point_ids,
        )

        print(
            f"Deleted {len(point_ids)} chunks "
            f"for document {document_id}."
        )

        return len(point_ids)