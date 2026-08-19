from pathlib import Path

from app.services.embedding_service import EmbeddingService
from app.services.pdf_parser import extract_text_from_pdf
from app.services.text_cleaner import clean_text
from app.services.chunker import create_chunks
from app.services.vector_store import VectorStore


COLLECTION_NAME = "privai_documents"


def process_document(
    pdf_path: str,
    document_id: str | None = None,
    embedding_service=None,
    hybrid_search_service=None,
    original_filename: str | None = None,
    user_id: str | None = None,
):
    """
    Process a PDF document and store its chunks and embeddings
    in Qdrant.

    Every indexed chunk is associated with a user_id.

    Pipeline:

        PDF
         ↓
        Extract text
         ↓
        Clean text
         ↓
        Chunk
         ↓
        BGE-M3 embeddings
         ↓
        Qdrant + user_id
         ↓
        Refresh user's BM25 index
    """

    # =========================================================
    # 1. Validate PDF
    # =========================================================

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    # =========================================================
    # 2. Validate user
    # =========================================================

    if not user_id:
        raise ValueError(
            "user_id is required when indexing "
            "a document."
        )

    # =========================================================
    # 3. Document ID
    # =========================================================

    if document_id is None:
        document_id = path.stem

    # =========================================================
    # 4. Original filename
    # =========================================================

    display_filename = (
        original_filename
        or path.name
    )

    print()
    print("=" * 60)

    print(
        f"Processing document: "
        f"{display_filename}"
    )

    print(
        f"Document ID: {document_id}"
    )

    print(
        f"User ID: {user_id}"
    )

    print("=" * 60)

    # =========================================================
    # 5. Extract PDF text
    # =========================================================

    print(
        "\nExtracting PDF text..."
    )

    document = extract_text_from_pdf(
        str(path)
    )

    print(
        f"Pages found: "
        f"{document['page_count']}"
    )

    # =========================================================
    # 6. Clean + chunk
    # =========================================================

    chunks = []

    for page in document["pages"]:

        page_number = page[
            "page_number"
        ]

        print(
            f"Processing page "
            f"{page_number}..."
        )

        cleaned_text = clean_text(
            page["text"]
        )

        page_chunks = create_chunks(
            cleaned_text
        )

        print(
            f"Chunks on page: "
            f"{len(page_chunks)}"
        )

        for chunk_index, chunk in enumerate(
            page_chunks
        ):

            chunks.append(
                {
                    "chunk_id": (
                        f"{document_id}"
                        f"-p{page_number}"
                        f"-c{chunk_index}"
                    ),

                    "document_id":
                        document_id,

                    "user_id":
                        user_id,

                    "filename":
                        display_filename,

                    "page_number":
                        page_number,

                    "chunk_index":
                        chunk_index,

                    "text":
                        chunk,
                }
            )

    print(
        f"\nCreated "
        f"{len(chunks)} chunks."
    )

    if not chunks:
        raise ValueError(
            "No text chunks were created "
            "from the PDF."
        )

    # =========================================================
    # 7. Generate embeddings
    # =========================================================

    print(
        "\nGenerating embeddings..."
    )

    if embedding_service is None:

        print(
            "No existing embedding service "
            "provided."
        )

        print(
            "Creating a new embedding service..."
        )

        embedding_service = (
            EmbeddingService()
        )

    else:

        print(
            "Reusing existing embedding service."
        )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = (
        embedding_service.embed_documents(
            texts
        )
    )

    print(
        f"Generated "
        f"{len(embeddings)} embeddings."
    )

    if not embeddings:
        raise ValueError(
            "Embedding generation returned "
            "no embeddings."
        )

    embedding_dimension = len(
        embeddings[0]
    )

    print(
        f"Embedding dimension: "
        f"{embedding_dimension}"
    )

    # =========================================================
    # 8. Connect to Qdrant
    # =========================================================

    print(
        "\nConnecting to Qdrant..."
    )

    vector_store = VectorStore()

    vector_store.create_collection(
        collection_name=COLLECTION_NAME,
        vector_size=embedding_dimension,
    )

    # =========================================================
    # 9. Store vectors
    # =========================================================

    print(
        "\nStoring chunks in Qdrant..."
    )

    vector_store.upsert_chunks(
        collection_name=COLLECTION_NAME,
        chunks=chunks,
        embeddings=embeddings,
        user_id=user_id,
    )

    print(
        f"Stored {len(chunks)} chunks in Qdrant "
        f"for user {user_id}."
    )

    # =========================================================
    # 10. Refresh USER-SCOPED BM25
    # =========================================================

    if hybrid_search_service is not None:

        print(
            "\nRefreshing BM25 index..."
        )

        hybrid_search_service.refresh_bm25_index(
            user_id=user_id
        )

        print(
            f"BM25 index refreshed for "
            f"user {user_id}."
        )

    # =========================================================
    # 11. Completion
    # =========================================================

    print()

    print("=" * 60)

    print(
        f"Successfully indexed "
        f"{len(chunks)} chunks."
    )

    print(
        f"Owner: {user_id}"
    )

    print(
        f"Filename: {display_filename}"
    )

    print("=" * 60)

    # =========================================================
    # 12. Return metadata
    # =========================================================

    return {
        "document_id":
            document_id,

        "user_id":
            user_id,

        "filename":
            display_filename,

        "page_count":
            document["page_count"],

        "chunk_count":
            len(chunks),

        "embedding_dimension":
            embedding_dimension,
    }


# =============================================================
# Manual testing
# =============================================================

if __name__ == "__main__":

    PDF_PATH = (
        "uploads/"
        "privai_rag_employee_policy_handbook.pdf"
    )

    # ---------------------------------------------------------
    # Manual development/testing only.
    #
    # Normal application uploads receive the authenticated
    # Google user's ID from FastAPI.
    # ---------------------------------------------------------

    TEST_USER_ID = (
        "manual-test-user"
    )

    result = process_document(
        pdf_path=PDF_PATH,
        user_id=TEST_USER_ID,
    )

    print(
        "\nDocument indexing completed:"
    )

    print(result)