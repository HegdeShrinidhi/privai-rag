import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.document_store import DocumentStore
from app.services.rag_service import RAGService


# ============================================================
# Environment
# ============================================================

load_dotenv()


# ============================================================
# Configuration
# ============================================================

COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION",
    "privai_documents",
)

UPLOAD_DIR = Path(
    os.getenv(
        "UPLOAD_DIR",
        "uploads",
    )
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="PrivAI-RAG API",
    description=(
        "Private enterprise Retrieval-Augmented "
        "Generation API."
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

frontend_url = os.getenv(
    "FRONTEND_URL"
)

if frontend_url:
    allowed_origins.append(
        frontend_url.rstrip("/")
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Global Services
# ============================================================

# IMPORTANT:
#
# RAGService is now lightweight.
#
# It DOES NOT load:
#
# - BGE-M3
# - BGE Reranker
# - Qwen
#
# during application startup.
#
# Those services are initialized lazily.

rag_service = RAGService(
    collection_name=COLLECTION_NAME
)

document_store = DocumentStore()


# ============================================================
# Document Status
# ============================================================

document_status: dict[
    str,
    dict
] = {}


# ============================================================
# Request Models
# ============================================================

class AskRequest(BaseModel):

    query: str

    document_id: str | None = None


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",

        "service": "PrivAI-RAG",

        "rag_service": (
            "initialized"
            if rag_service is not None
            else "not_initialized"
        ),

        "collection": COLLECTION_NAME,
    }


# ============================================================
# Root
# ============================================================

@app.get("/")
def root():

    return {
        "message": "PrivAI-RAG API",

        "status": "running",

        "docs": "/docs",

        "health": "/health",
    }


# ============================================================
# Process Document
# ============================================================

def process_document(
    document_id: str,
    file_path: str,
    filename: str,
    user_id: str,
):
    """
    Background document processing.

    ML retrieval components are initialized here,
    rather than during FastAPI startup.
    """

    try:

        print()
        print("=" * 60)

        print(
            f"Processing document: {filename}"
        )

        print(
            f"Document ID: {document_id}"
        )

        print(
            f"User: {user_id}"
        )

        print("=" * 60)

        document_status[
            document_id
        ] = {
            "status": "processing",

            "filename": filename,
        }

        # =====================================================
        # IMPORTANT
        # =====================================================
        #
        # Initialize only the retrieval components.
        #
        # This loads BGE-M3 when a document actually needs
        # to be indexed.
        #
        # It does NOT load the reranker or LLM.
        #

        rag_service._initialize_retrieval()

        embedding_service = (
            rag_service.embedding_service
        )

        hybrid_search_service = (
            rag_service.hybrid_search
        )

        # =====================================================
        # Validate Services
        # =====================================================

        if embedding_service is None:

            raise RuntimeError(
                "Embedding service failed to initialize."
            )

        if hybrid_search_service is None:

            raise RuntimeError(
                "Hybrid search service failed "
                "to initialize."
            )

        # =====================================================
        # Document Processing
        # =====================================================
        #
        # IMPORTANT:
        #
        # Keep the existing DocumentStore/indexing flow.
        # The actual indexing implementation belongs to the
        # existing services in your project.
        #

        print(
            "Processing PDF..."
        )

        # -----------------------------------------------------
        # Try the existing DocumentStore interface.
        # -----------------------------------------------------

        result = None

        if hasattr(
            document_store,
            "process_document",
        ):

            result = (
                document_store.process_document(
                    file_path=file_path,

                    document_id=document_id,

                    filename=filename,

                    user_id=user_id,

                    embedding_service=(
                        embedding_service
                    ),

                    vector_store=(
                        hybrid_search_service.vector_store
                        if hasattr(
                            hybrid_search_service,
                            "vector_store",
                        )
                        else None
                    ),
                )
            )

        else:

            # -------------------------------------------------
            # If the existing application has its own
            # indexing function, do not silently invent a
            # different indexing pipeline.
            # -------------------------------------------------

            raise RuntimeError(
                "DocumentStore does not expose "
                "process_document(). "
                "Use the existing document indexing "
                "function from your project."
            )

        # =====================================================
        # Completed
        # =====================================================

        document_status[
            document_id
        ] = {
            "status": "completed",

            "filename": filename,
        }

        print(
            f"Document completed: {filename}"
        )

    except Exception as exc:

        print()
        print("=" * 60)

        print(
            f"Document processing failed: "
            f"{filename}"
        )

        print(
            f"User: {user_id}"
        )

        print(
            f"Error: {exc}"
        )

        print("=" * 60)

        document_status[
            document_id
        ] = {
            "status": "failed",

            "filename": filename,

            "error": str(exc),
        }

    finally:

        # =====================================================
        # Remove temporary uploaded file
        # =====================================================

        try:

            path = Path(
                file_path
            )

            if path.exists():

                path.unlink()

                print(
                    f"Removed temporary file: "
                    f"{file_path}"
                )

        except Exception as cleanup_error:

            print(
                "Failed to remove temporary "
                f"file: {cleanup_error}"
            )


# ============================================================
# Upload Document
# ============================================================

@app.post(
    "/documents/upload"
)
async def upload_document(
    background_tasks: BackgroundTasks,

    file: UploadFile = File(...),

    x_user_id: str | None = Header(
        default=None
    ),
):

    # =========================================================
    # Validate User
    # =========================================================

    if not x_user_id:

        raise HTTPException(
            status_code=401,

            detail=(
                "X-User-ID header is required."
            ),
        )

    user_id = x_user_id.strip()

    if not user_id:

        raise HTTPException(
            status_code=401,

            detail="Invalid user ID.",
        )

    # =========================================================
    # Validate File
    # =========================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,

            detail="Filename is required.",
        )

    filename = file.filename

    if not filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,

            detail=(
                "Only PDF files are supported."
            ),
        )

    # =========================================================
    # Generate Document ID
    # =========================================================

    document_id = str(
        uuid.uuid4()
    )

    # =========================================================
    # Save File
    # =========================================================

    file_path = (
        UPLOAD_DIR
        / f"{document_id}.pdf"
    )

    try:

        contents = await file.read()

        if not contents:

            raise HTTPException(
                status_code=400,

                detail=(
                    "Uploaded file is empty."
                ),
            )

        with open(
            file_path,
            "wb",
        ) as output:

            output.write(
                contents
            )

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,

            detail=(
                "Failed to save uploaded "
                f"file: {exc}"
            ),
        )

    # =========================================================
    # Initial Status
    # =========================================================

    document_status[
        document_id
    ] = {
        "status": "queued",

        "filename": filename,
    }

    # =========================================================
    # Background Processing
    # =========================================================

    background_tasks.add_task(
        process_document,

        document_id,

        str(file_path),

        filename,

        user_id,
    )

    # =========================================================
    # Response
    # =========================================================

    return {
        "document_id": document_id,

        "filename": filename,

        "status": "queued",

        "message": (
            "Document uploaded successfully "
            "and processing has started."
        ),
    }


# ============================================================
# Document Status
# ============================================================

@app.get(
    "/documents/{document_id}/status"
)
def get_document_status(
    document_id: str,

    x_user_id: str | None = Header(
        default=None
    ),
):

    if not x_user_id:

        raise HTTPException(
            status_code=401,

            detail=(
                "X-User-ID header is required."
            ),
        )

    status = document_status.get(
        document_id
    )

    if status is None:

        return {
            "document_id": document_id,

            "status": "unknown",
        }

    return {
        "document_id": document_id,

        **status,
    }


# ============================================================
# Get Documents
# ============================================================

@app.get(
    "/documents"
)
def get_documents(
    x_user_id: str | None = Header(
        default=None
    ),
):

    if not x_user_id:

        raise HTTPException(
            status_code=401,

            detail=(
                "X-User-ID header is required."
            ),
        )

    user_id = x_user_id.strip()

    try:

        # -----------------------------------------------------
        # We only need the retrieval service here so that
        # Qdrant access is available.
        #
        # -----------------------------------------------------

        rag_service._initialize_retrieval()

        if rag_service.hybrid_search is None:

            raise RuntimeError(
                "Hybrid search service "
                "is not initialized."
            )

        # -----------------------------------------------------
        # Use the existing VectorStore document retrieval.
        #
        # This avoids inventing a new HybridSearch method.
        # -----------------------------------------------------

        vector_store = (
            rag_service.hybrid_search.vector_store
        )

        points = (
            vector_store.get_all_points(
                collection_name=COLLECTION_NAME,

                user_id=user_id,
            )
        )

        # -----------------------------------------------------
        # Convert chunks into document-level results.
        # -----------------------------------------------------

        documents = {}

        for point in points:

            payload = (
                point.payload or {}
            )

            document_id = payload.get(
                "document_id"
            )

            if not document_id:

                continue

            if document_id not in documents:

                documents[
                    document_id
                ] = {
                    "document_id": document_id,

                    "filename": payload.get(
                        "filename",
                        "Unknown",
                    ),

                    "user_id": payload.get(
                        "user_id"
                    ),

                    "status": (
                        document_status
                        .get(
                            document_id,
                            {}
                        )
                        .get(
                            "status",
                            "completed",
                        )
                    ),
                }

        return {
            "documents": list(
                documents.values()
            )
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,

            detail=(
                "Failed to retrieve "
                f"documents: {exc}"
            ),
        )


# ============================================================
# Delete Document
# ============================================================

@app.delete(
    "/documents/{document_id}"
)
def delete_document(
    document_id: str,

    x_user_id: str | None = Header(
        default=None
    ),
):

    if not x_user_id:

        raise HTTPException(
            status_code=401,

            detail=(
                "X-User-ID header is required."
            ),
        )

    user_id = x_user_id.strip()

    try:

        # -----------------------------------------------------
        # Initialize retrieval so VectorStore is available.
        # -----------------------------------------------------

        rag_service._initialize_retrieval()

        vector_store = (
            rag_service.hybrid_search.vector_store
        )

        deleted_count = (
            vector_store.delete_document(
                collection_name=(
                    COLLECTION_NAME
                ),

                document_id=document_id,

                user_id=user_id,
            )
        )

        document_status.pop(
            document_id,
            None,
        )

        return {
            "document_id": document_id,

            "deleted": (
                deleted_count > 0
            ),

            "deleted_chunks": (
                deleted_count
            ),

            "message": (
                "Document deleted successfully."
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,

            detail=(
                "Failed to delete "
                f"document: {exc}"
            ),
        )


# ============================================================
# Ask Question
# ============================================================

@app.post(
    "/ask"
)
def ask_question(
    request: AskRequest,

    x_user_id: str | None = Header(
        default=None
    ),
):

    if not x_user_id:

        raise HTTPException(
            status_code=401,

            detail=(
                "X-User-ID header is required."
            ),
        )

    user_id = x_user_id.strip()

    # =========================================================
    # Validate Query
    # =========================================================

    if not request.query.strip():

        raise HTTPException(
            status_code=400,

            detail=(
                "Query cannot be empty."
            ),
        )

    try:

        print()
        print("=" * 60)

        print(
            f"Processing query: "
            f"{request.query}"
        )

        print(
            f"Authenticated user: "
            f"{user_id}"
        )

        if request.document_id:

            print(
                f"Document filter: "
                f"{request.document_id}"
            )

        else:

            print(
                "Document filter: "
                "ALL USER DOCUMENTS"
            )

        print("=" * 60)

        # =====================================================
        # RAGService.ask() performs lazy initialization:
        #
        # BGE-M3
        # BGE Reranker
        # Qwen
        #
        # only when they are actually needed.
        # =====================================================

        result = rag_service.ask(
            query=request.query,

            user_id=user_id,

            document_id=request.document_id,
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,

            detail=str(exc),
        )

    except Exception as exc:

        print(
            f"RAG request failed: {exc}"
        )

        raise HTTPException(
            status_code=500,

            detail=(
                "Failed to process the "
                f"question: {exc}"
            ),
        )


# ============================================================
# Startup
# ============================================================

@app.on_event(
    "startup"
)
def startup_event():

    print()
    print("=" * 60)

    print(
        "Starting PrivAI-RAG..."
    )

    print("=" * 60)

    print(
        "RAG service created."
    )

    print(
        "ML models are configured for "
        "lazy loading."
    )

    print(
        "BGE-M3, BGE-Reranker and Qwen "
        "will not load during startup."
    )

    print(
        "PrivAI-RAG ready."
    )

    print("=" * 60)