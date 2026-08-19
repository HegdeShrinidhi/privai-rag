import re
from typing import Any


class BM25Service:
    """
    BM25 keyword-based retrieval service.

    Supports:

    - User-level filtering
    - Document-level filtering
    - Names
    - Numbers
    - Dates
    - Exact phrases
    - Policy terms
    - Technical terminology

    Security model:

        user_id
            ↓
        only that user's chunks

        optional document_id
            ↓
        only that user's specific document
    """

    def __init__(self):
        self.documents: list[
            dict[str, Any]
        ] = []

        self.bm25 = None

    # =========================================================
    # Tokenizer
    # =========================================================

    def _tokenize(
        self,
        text: str,
    ) -> list[str]:
        """
        Convert text into normalized tokens.
        """

        if not text:
            return []

        text = text.lower()

        tokens = re.findall(
            r"\b\w+\b",
            text,
        )

        return tokens

    # =========================================================
    # Build Index
    # =========================================================

    def build_index(
        self,
        documents: list[dict[str, Any]],
    ):
        """
        Build BM25 index from document chunks.

        The complete collection is indexed once.

        User isolation is applied during search.
        """

        from rank_bm25 import BM25Okapi

        self.documents = documents

        tokenized_documents = [
            self._tokenize(
                document.get(
                    "text",
                    "",
                )
            )
            for document in documents
        ]

        # -----------------------------------------------------
        # Handle empty collection
        # -----------------------------------------------------

        if not tokenized_documents:

            self.bm25 = None

            print(
                "BM25 index built with 0 documents."
            )

            return

        self.bm25 = BM25Okapi(
            tokenized_documents
        )

        print(
            f"BM25 index built with "
            f"{len(documents)} documents."
        )

    # =========================================================
    # Search
    # =========================================================

    def search(
        self,
        query: str,
        limit: int = 5,
        user_id: str | None = None,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search using BM25.

        Parameters
        ----------
        query:
            User's search question.

        limit:
            Maximum number of results.

        user_id:
            Authenticated user's ID.

            This is required for normal application
            searches and prevents cross-user retrieval.

        document_id:
            Optional document restriction.

            If supplied, results must belong to both:

                user_id
                +
                document_id
        """

        # -----------------------------------------------------
        # BM25 not initialized
        # -----------------------------------------------------

        if self.bm25 is None:
            return []

        # -----------------------------------------------------
        # User identity is required
        # -----------------------------------------------------

        if not user_id:

            raise ValueError(
                "user_id is required for BM25 search."
            )

        # -----------------------------------------------------
        # Empty query
        # -----------------------------------------------------

        if not query or not query.strip():
            return []

        query_tokens = self._tokenize(
            query
        )

        if not query_tokens:
            return []

        # -----------------------------------------------------
        # Calculate BM25 scores
        # -----------------------------------------------------

        scores = self.bm25.get_scores(
            query_tokens
        )

        # -----------------------------------------------------
        # Build candidate indices
        #
        # IMPORTANT:
        #
        # We filter by user_id BEFORE returning results.
        # -----------------------------------------------------

        candidate_indices = []

        for index, document in enumerate(
            self.documents
        ):

            # -------------------------------------------------
            # User isolation
            # -------------------------------------------------

            if document.get(
                "user_id"
            ) != user_id:

                continue

            # -------------------------------------------------
            # Optional document isolation
            # -------------------------------------------------

            if document_id is not None:

                if document.get(
                    "document_id"
                ) != document_id:

                    continue

            candidate_indices.append(
                index
            )

        # -----------------------------------------------------
        # No documents belonging to this user
        # -----------------------------------------------------

        if not candidate_indices:
            return []

        # -----------------------------------------------------
        # Rank candidates
        # -----------------------------------------------------

        ranked_indices = sorted(
            candidate_indices,
            key=lambda index:
                scores[index],
            reverse=True,
        )

        # -----------------------------------------------------
        # Build results
        # -----------------------------------------------------

        results = []

        for index in ranked_indices[
            :limit
        ]:

            document = dict(
                self.documents[index]
            )

            document["score"] = float(
                scores[index]
            )

            results.append(
                document
            )

        return results