from app.services.hybrid_search import HybridSearchService
from app.services.reranker import RerankerService
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService


class RAGService:
    """
    End-to-end Retrieval-Augmented Generation pipeline.

    Query
      ↓
    User-scoped Hybrid Search
      ↓
    BGE Reranker
      ↓
    Relevance Filtering
      ↓
    Context Builder
      ↓
    Local LLM
      ↓
    Answer + Citations

    Security:

    user_id
      ↓
    Vector Search + BM25
      ↓
    Only user's documents
    """

    def __init__(
        self,
        collection_name: str = "privai_documents",
    ):
        print(
            "Initializing RAG service..."
        )

        # =====================================================
        # Embedding Service
        # =====================================================

        print(
            "Loading embedding service..."
        )

        self.embedding_service = (
            EmbeddingService()
        )

        # =====================================================
        # Hybrid Search
        # =====================================================

        print(
            "Initializing hybrid search..."
        )

        self.hybrid_search = (
            HybridSearchService(
                collection_name=collection_name,
                embedding_service=(
                    self.embedding_service
                ),
            )
        )

        # =====================================================
        # Reranker
        # =====================================================

        print(
            "Loading reranker..."
        )

        self.reranker = (
            RerankerService()
        )

        # =====================================================
        # Local LLM
        # =====================================================

        print(
            "Loading local LLM..."
        )

        self.llm = LLMService()

        print(
            "RAG service initialized successfully."
        )

    # =========================================================
    # Context Builder
    # =========================================================

    def build_context(
        self,
        documents: list[dict],
    ) -> str:
        """
        Build a clean context from relevant documents.
        """

        if not documents:
            return ""

        context_parts = []

        for index, document in enumerate(
            documents,
            start=1,
        ):

            context_parts.append(
                f"""
SOURCE {index}
Document: {document["filename"]}
Page: {document["page_number"]}
Section/Chunk: {document["chunk_index"]}

Content:
{document["text"]}
""".strip()
            )

        return "\n\n".join(
            context_parts
        )

    # =========================================================
    # Prompt Builder
    # =========================================================

    def build_prompt(
        self,
        query: str,
        context: str,
    ) -> str:
        """
        Build a strict grounded-generation prompt.
        """

        return f"""
You are an enterprise document assistant.

Answer the user's question using ONLY the provided
document context.

STRICT RULES:

1. Use only information contained in the context.
2. Never use outside knowledge.
3. Never guess or invent information.
4. If the answer cannot be found in the context,
   say exactly:

"I could not find this information in the provided documents."

5. Give a concise factual answer.
6. Do not mention information unrelated to the question.
7. Do not repeat the entire context.
8. Preserve numbers, dates, names, policy requirements,
   and deadlines exactly as they appear in the context.
9. Do not make assumptions.
10. Do not use your general knowledge to complete missing
    information.

DOCUMENT CONTEXT:

{context}

USER QUESTION:

{query}

ANSWER:
""".strip()

    # =========================================================
    # Relevance Filtering
    # =========================================================

    def filter_documents(
        self,
        documents: list[dict],
        threshold: float = 0.10,
        max_documents: int = 2,
    ) -> list[dict]:
        """
        Keep only sufficiently relevant reranked documents.

        The BGE reranker score is used for ranking/filtering.
        It is NOT an accuracy percentage.
        """

        if not documents:
            return []

        filtered = [
            document
            for document in documents
            if document.get(
                "reranker_score",
                0.0,
            ) >= threshold
        ]

        # Always keep the best result if retrieval returned
        # something, even if it is below the threshold.

        if not filtered:
            filtered = [
                documents[0]
            ]

        return filtered[
            :max_documents
        ]

    # =========================================================
    # Sources
    # =========================================================

    def build_sources(
        self,
        documents: list[dict],
    ) -> list[dict]:
        """
        Build clean citation metadata.
        """

        sources = []

        for document in documents:

            sources.append(
                {
                    "document_id": document.get(
                        "document_id"
                    ),

                    "filename": document[
                        "filename"
                    ],

                    "page_number": document[
                        "page_number"
                    ],

                    "chunk_index": document[
                        "chunk_index"
                    ],

                    "reranker_score": round(
                        document.get(
                            "reranker_score",
                            0.0,
                        ),
                        4,
                    ),
                }
            )

        return sources

    # =========================================================
    # Main RAG Pipeline
    # =========================================================

    def ask(
        self,
        query: str,
        user_id: str,
        document_id: str | None = None,
        retrieval_limit: int = 5,
        rerank_limit: int = 5,
        relevance_threshold: float = 0.10,
        max_context_documents: int = 2,
    ) -> dict:
        """
        Execute the complete RAG pipeline.

        Parameters
        ----------
        query:
            User's question.

        user_id:
            Authenticated user's identity.

            REQUIRED.

            All retrieval is restricted to this user.

        document_id:
            Optional document restriction.

            If supplied, retrieval is restricted to that
            document AND the authenticated user.

        retrieval_limit:
            Number of hybrid retrieval candidates.

        rerank_limit:
            Number of candidates passed to the reranker.

        relevance_threshold:
            Minimum reranker score.

        max_context_documents:
            Maximum number of documents/chunks used as context.
        """

        # =====================================================
        # Validate user
        # =====================================================

        if not user_id:

            raise ValueError(
                "user_id is required for RAG search."
            )

        # =====================================================
        # Validate query
        # =====================================================

        if not query or not query.strip():

            raise ValueError(
                "query cannot be empty."
            )

        print(
            f"\nProcessing query: {query}"
        )

        print(
            f"Authenticated user: {user_id}"
        )

        # =====================================================
        # Document Scope
        # =====================================================

        if document_id:

            print(
                f"Document filter: "
                f"{document_id}"
            )

        else:

            print(
                "Document filter: "
                "ALL USER DOCUMENTS"
            )

        # =====================================================
        # 1. User-scoped Hybrid Retrieval
        # =====================================================

        print(
            "Running user-scoped hybrid retrieval..."
        )

        hybrid_results = (
            self.hybrid_search.search(
                query=query,

                limit=retrieval_limit,

                vector_weight=0.6,

                bm25_weight=0.4,

                user_id=user_id,

                document_id=document_id,
            )
        )

        print(
            f"Retrieved "
            f"{len(hybrid_results)} candidates "
            f"for user {user_id}."
        )

        # =====================================================
        # Defensive ownership check
        # =====================================================

        hybrid_results = [
            document
            for document in hybrid_results
            if document.get(
                "user_id"
            ) == user_id
        ]

        # =====================================================
        # No Retrieval Results
        # =====================================================

        if not hybrid_results:

            answer = (
                "I could not find this information "
                "in the provided documents."
            )

            return {
                "query": query,

                "answer": answer,

                "sources": [],

                "context_documents": [],
            }

        # =====================================================
        # 2. Reranking
        # =====================================================

        print(
            "Running BGE reranker..."
        )

        reranked_results = (
            self.reranker.rerank(
                query=query,

                documents=hybrid_results,

                top_k=rerank_limit,
            )
        )

        print(
            f"Reranked "
            f"{len(reranked_results)} candidates."
        )

        # =====================================================
        # Defensive ownership check after reranking
        # =====================================================

        reranked_results = [
            document
            for document in reranked_results
            if document.get(
                "user_id"
            ) == user_id
        ]

        # =====================================================
        # 3. Relevance Filtering
        # =====================================================

        filtered_results = (
            self.filter_documents(
                documents=reranked_results,

                threshold=relevance_threshold,

                max_documents=max_context_documents,
            )
        )

        print(
            f"Selected "
            f"{len(filtered_results)} relevant "
            f"documents for context."
        )

        # =====================================================
        # 4. Final Ownership Check
        # =====================================================

        filtered_results = [
            document
            for document in filtered_results
            if document.get(
                "user_id"
            ) == user_id
        ]

        # =====================================================
        # 5. No Relevant Context
        # =====================================================

        if not filtered_results:

            answer = (
                "I could not find this information "
                "in the provided documents."
            )

            return {
                "query": query,

                "answer": answer,

                "sources": [],

                "context_documents": [],
            }

        # =====================================================
        # 6. Build Context
        # =====================================================

        context = self.build_context(
            filtered_results
        )

        # =====================================================
        # 7. Build Grounded Prompt
        # =====================================================

        prompt = self.build_prompt(
            query=query,
            context=context,
        )

        # =====================================================
        # 8. Generate Answer
        # =====================================================

        print(
            "Generating answer with local LLM..."
        )

        answer = self.llm.generate(
            prompt=prompt,
            max_new_tokens=150,
        )

        # =====================================================
        # 9. Build Sources
        # =====================================================

        sources = self.build_sources(
            filtered_results
        )

        # =====================================================
        # 10. Return Complete Result
        # =====================================================

        return {
            "query": query,

            "answer": answer,

            "sources": sources,

            "context_documents": filtered_results,
        }