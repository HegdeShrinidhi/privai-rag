from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.bm25_service import BM25Service
from app.services.document_store import DocumentStore


class HybridSearchService:
    """
    User-isolated hybrid retrieval service.

    Retrieval pipeline:

        User Query
            ↓
        ┌───────────────┐
        │ Vector Search │
        │   Qdrant      │
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │ BM25 Search   │
        │ User-scoped   │
        └───────┬───────┘
                │
                ▼
        Score Normalization
                ↓
        Weighted Hybrid Score
                ↓
        Top Results

    Security:

        user_id
            ↓
        Vector Search → only user's chunks
            ↓
        BM25 → only user's chunks
            ↓
        Hybrid Merge → only user's chunks
    """

    def __init__(
        self,
        collection_name: str = "privai_documents",
        embedding_service=None,
    ):
        self.collection_name = collection_name

        # =====================================================
        # Embedding Service
        # =====================================================

        if embedding_service is not None:

            self.embedding_service = (
                embedding_service
            )

        else:

            self.embedding_service = (
                EmbeddingService()
            )

        # =====================================================
        # Vector Store
        # =====================================================

        self.vector_store = VectorStore()

        # =====================================================
        # Document Store
        # =====================================================

        self.document_store = (
            DocumentStore()
        )

        # =====================================================
        # User-scoped BM25 indexes
        #
        # Example:
        #
        # {
        #     "userA@gmail.com": BM25Service(),
        #     "userB@gmail.com": BM25Service()
        # }
        #
        # Each user gets an independent BM25 index.
        # =====================================================

        self.bm25_indexes: dict[
            str,
            BM25Service,
        ] = {}

        # =====================================================
        # Track loaded users
        # =====================================================

        self.loaded_users: set[str] = set()

        print(
            "Hybrid search service initialized."
        )

    # =========================================================
    # Get User BM25 Service
    # =========================================================

    def _get_user_bm25(
        self,
        user_id: str,
    ) -> BM25Service:
        """
        Get or create a BM25 service for a specific user.
        """

        if not user_id:

            raise ValueError(
                "user_id is required."
            )

        if (
            user_id
            not in self.bm25_indexes
        ):

            print(
                f"Creating BM25 index "
                f"for user: {user_id}"
            )

            self.bm25_indexes[
                user_id
            ] = BM25Service()

        return self.bm25_indexes[
            user_id
        ]

    # =========================================================
    # Build User BM25 Index
    # =========================================================

    def refresh_user_bm25_index(
        self,
        user_id: str,
    ):
        """
        Build or refresh the BM25 index for one user.

        Only that user's Qdrant chunks are loaded.
        """

        if not user_id:

            raise ValueError(
                "user_id is required."
            )

        print(
            f"\nRefreshing BM25 index "
            f"for user: {user_id}"
        )

        # -----------------------------------------------------
        # Retrieve ONLY this user's chunks.
        # -----------------------------------------------------

        documents = (
            self.document_store.get_all_chunks(
                collection_name=self.collection_name,
                user_id=user_id,
            )
        )

        # -----------------------------------------------------
        # Get user's BM25 instance.
        # -----------------------------------------------------

        bm25_service = (
            self._get_user_bm25(
                user_id
            )
        )

        # -----------------------------------------------------
        # Build index.
        # -----------------------------------------------------

        bm25_service.build_index(
            documents
        )

        self.loaded_users.add(
            user_id
        )

        print(
            f"BM25 index refreshed for "
            f"{user_id} with "
            f"{len(documents)} chunks."
        )

    # =========================================================
    # Refresh BM25 Index
    # =========================================================

    def refresh_bm25_index(
        self,
        user_id: str | None = None,
    ):
        """
        Refresh BM25 indexes.

        If user_id is provided:
            refresh only that user's index.

        If user_id is omitted:
            existing user indexes are refreshed.

        New authenticated users are normally initialized
        automatically when they perform their first search.
        """

        # -----------------------------------------------------
        # Specific user
        # -----------------------------------------------------

        if user_id:

            self.refresh_user_bm25_index(
                user_id
            )

            return

        # -----------------------------------------------------
        # Refresh all already-known users
        # -----------------------------------------------------

        if not self.loaded_users:

            print(
                "No user BM25 indexes "
                "currently loaded."
            )

            return

        for existing_user_id in list(
            self.loaded_users
        ):

            self.refresh_user_bm25_index(
                existing_user_id
            )

    # =========================================================
    # Normalize Scores
    # =========================================================

    @staticmethod
    def normalize_scores(
        results: list[dict],
        score_key: str,
    ) -> list[dict]:
        """
        Normalize scores to [0, 1] using min-max scaling.
        """

        if not results:
            return []

        scores = [
            float(
                result.get(
                    score_key,
                    0.0,
                )
            )
            for result in results
        ]

        min_score = min(
            scores
        )

        max_score = max(
            scores
        )

        # -----------------------------------------------------
        # All scores identical
        # -----------------------------------------------------

        if max_score == min_score:

            for result in results:

                result[
                    "normalized_score"
                ] = 1.0

            return results

        # -----------------------------------------------------
        # Min-max normalization
        # -----------------------------------------------------

        for result in results:

            result[
                "normalized_score"
            ] = (
                float(
                    result.get(
                        score_key,
                        0.0,
                    )
                )
                - min_score
            ) / (
                max_score
                - min_score
            )

        return results

    # =========================================================
    # Search
    # =========================================================

    def search(
        self,
        query: str,
        limit: int = 5,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        user_id: str | None = None,
        document_id: str | None = None,
    ) -> list[dict]:
        """
        Perform user-isolated hybrid search.

        Parameters
        ----------
        query:
            User's natural-language question.

        limit:
            Maximum number of final results.

        vector_weight:
            Weight assigned to vector search.

        bm25_weight:
            Weight assigned to BM25.

        user_id:
            REQUIRED authenticated user identity.

        document_id:
            Optional specific document filter.
        """

        # =====================================================
        # Validate user
        # =====================================================

        if not user_id:

            raise ValueError(
                "user_id is required for "
                "hybrid search."
            )

        # =====================================================
        # Validate query
        # =====================================================

        if not query or not query.strip():

            return []

        # =====================================================
        # Validate weights
        # =====================================================

        if vector_weight < 0:

            raise ValueError(
                "vector_weight cannot be negative."
            )

        if bm25_weight < 0:

            raise ValueError(
                "bm25_weight cannot be negative."
            )

        if (
            vector_weight == 0
            and bm25_weight == 0
        ):

            raise ValueError(
                "At least one search weight "
                "must be greater than zero."
            )

        # =====================================================
        # 1. Ensure user's BM25 index exists
        # =====================================================

        if (
            user_id
            not in self.bm25_indexes
        ):

            print(
                f"No BM25 index found for "
                f"user {user_id}."
            )

            self.refresh_user_bm25_index(
                user_id
            )

        # =====================================================
        # 2. Vector Search
        # =====================================================

        print(
            "\nRunning vector search..."
        )

        query_vector = (
            self.embedding_service.embed_query(
                query
            )
        )

        vector_results = (
            self.vector_store.search(
                collection_name=(
                    self.collection_name
                ),

                query_vector=query_vector,

                limit=limit,

                user_id=user_id,

                document_id=document_id,
            )
        )

        print(
            f"Vector search returned "
            f"{len(vector_results)} results "
            f"for user {user_id}."
        )

        vector_documents = []

        for result in vector_results:

            payload = (
                result.payload or {}
            )

            # -------------------------------------------------
            # Defensive user isolation
            # -------------------------------------------------

            if payload.get(
                "user_id"
            ) != user_id:

                continue

            # -------------------------------------------------
            # Defensive document isolation
            # -------------------------------------------------

            if (
                document_id is not None
                and payload.get(
                    "document_id"
                ) != document_id
            ):

                continue

            vector_documents.append(
                {
                    "user_id":
                        payload.get(
                            "user_id"
                        ),

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

                    "vector_score":
                        float(
                            result.score
                        ),
                }
            )

        # =====================================================
        # 3. BM25 Search
        # =====================================================

        print(
            "\nRunning user-scoped BM25 search..."
        )

        bm25_service = (
            self.bm25_indexes[
                user_id
            ]
        )

        bm25_results = (
            bm25_service.search(
                query=query,

                limit=limit,

                user_id=user_id,

                document_id=document_id,
            )
        )

        print(
            f"BM25 search returned "
            f"{len(bm25_results)} results "
            f"for user {user_id}."
        )

        bm25_documents = []

        for result in bm25_results:

            # -------------------------------------------------
            # Defensive ownership check
            # -------------------------------------------------

            if result.get(
                "user_id"
            ) != user_id:

                continue

            # -------------------------------------------------
            # Defensive document check
            # -------------------------------------------------

            if (
                document_id is not None
                and result.get(
                    "document_id"
                ) != document_id
            ):

                continue

            bm25_documents.append(
                {
                    "user_id":
                        result.get(
                            "user_id"
                        ),

                    "chunk_id":
                        result.get(
                            "chunk_id"
                        ),

                    "document_id":
                        result.get(
                            "document_id"
                        ),

                    "filename":
                        result.get(
                            "filename"
                        ),

                    "page_number":
                        result.get(
                            "page_number"
                        ),

                    "chunk_index":
                        result.get(
                            "chunk_index"
                        ),

                    "text":
                        result.get(
                            "text"
                        ),

                    "bm25_score":
                        float(
                            result.get(
                                "score",
                                0.0,
                            )
                        ),
                }
            )

        # =====================================================
        # 4. Normalize Vector Scores
        # =====================================================

        vector_documents = (
            self.normalize_scores(
                vector_documents,
                score_key="vector_score",
            )
        )

        # =====================================================
        # 5. Normalize BM25 Scores
        # =====================================================

        bm25_documents = (
            self.normalize_scores(
                bm25_documents,
                score_key="bm25_score",
            )
        )

        # =====================================================
        # 6. Merge Results
        # =====================================================

        merged: dict[
            str,
            dict
        ] = {}

        # -----------------------------------------------------
        # Add vector results
        # -----------------------------------------------------

        for document in vector_documents:

            chunk_id = document.get(
                "chunk_id"
            )

            if not chunk_id:
                continue

            merged[
                chunk_id
            ] = {
                **document,

                "vector_score":
                    document.get(
                        "vector_score",
                        0.0,
                    ),

                "vector_normalized":
                    document.get(
                        "normalized_score",
                        0.0,
                    ),

                "bm25_score":
                    0.0,

                "bm25_normalized":
                    0.0,
            }

        # -----------------------------------------------------
        # Add / merge BM25 results
        # -----------------------------------------------------

        for document in bm25_documents:

            chunk_id = document.get(
                "chunk_id"
            )

            if not chunk_id:
                continue

            if chunk_id not in merged:

                merged[
                    chunk_id
                ] = {
                    **document,

                    "vector_score":
                        0.0,

                    "vector_normalized":
                        0.0,

                    "bm25_score":
                        document.get(
                            "bm25_score",
                            0.0,
                        ),

                    "bm25_normalized":
                        document.get(
                            "normalized_score",
                            0.0,
                        ),
                }

            else:

                merged[
                    chunk_id
                ][
                    "bm25_score"
                ] = document.get(
                    "bm25_score",
                    0.0,
                )

                merged[
                    chunk_id
                ][
                    "bm25_normalized"
                ] = document.get(
                    "normalized_score",
                    0.0,
                )

        # =====================================================
        # 7. Calculate Hybrid Score
        # =====================================================

        results = list(
            merged.values()
        )

        for result in results:

            result[
                "hybrid_score"
            ] = (
                vector_weight
                * result.get(
                    "vector_normalized",
                    0.0,
                )
                +
                bm25_weight
                * result.get(
                    "bm25_normalized",
                    0.0,
                )
            )

        # =====================================================
        # 8. Sort by Hybrid Score
        # =====================================================

        results.sort(
            key=lambda result:
                result.get(
                    "hybrid_score",
                    0.0,
                ),
            reverse=True,
        )

        # =====================================================
        # 9. Final Security Filter
        # =====================================================

        secure_results = []

        for result in results:

            # -------------------------------------------------
            # User must match
            # -------------------------------------------------

            if result.get(
                "user_id"
            ) != user_id:

                continue

            # -------------------------------------------------
            # Document must match if specified
            # -------------------------------------------------

            if (
                document_id is not None
                and result.get(
                    "document_id"
                ) != document_id
            ):

                continue

            secure_results.append(
                result
            )

        # =====================================================
        # 10. Return Top Results
        # =====================================================

        return secure_results[
            :limit
        ]