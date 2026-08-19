import shutil
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

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

from app.services.rag_service import RAGService
from index_document import process_document


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="PrivAI-RAG",
    description="Enterprise Document RAG API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Configuration
# ============================================================

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

ALLOWED_EXTENSIONS = {
    ".pdf",
}

COLLECTION_NAME = "privai_documents"


# ============================================================
# Document Processing Status
# ============================================================

document_status: dict[str, dict] = {}


# ============================================================
# Request Models
# ============================================================

class AskRequest(BaseModel):
    question: str
    document_id: str | None = None


# ============================================================
# Global RAG Service
# ============================================================

rag_service = None


# ============================================================
# User Identity
# ============================================================

def get_user_id(
    x_user_id: str | None = Header(
        default=None,
        alias="X-User-ID",
    ),
) -> str:
    """
    Get the authenticated user's identity
    from the request header.

    Current development authentication bridge:

        X-User-ID: user@example.com

    IMPORTANT:

    This is an intermediate backend integration step.

    In the final production architecture, this value
    must come from a verified Auth.js authentication
    bridge rather than trusting a browser-provided header.
    """

    if not x_user_id:

        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required. "
                "Missing X-User-ID header."
            ),
        )

    user_id = x_user_id.strip()

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Invalid user identity.",
        )

    return user_id


# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
def startup_event():

    global rag_service

    print("=" * 60)
    print("Starting PrivAI-RAG...")
    print("=" * 60)

    print(
        "Loading RAG components..."
    )

    rag_service = RAGService(
        collection_name=COLLECTION_NAME
    )

    print(
        "PrivAI-RAG ready."
    )

    print("=" * 60)


# ============================================================
# Root
# ============================================================

@app.get("/")
def root():

    return {
        "project": "PrivAI-RAG",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "rag_service": (
            "ready"
            if rag_service is not None
            else "not_ready"
        ),
    }


# ============================================================
# Background Document Processing
# ============================================================

def process_uploaded_document(
    file_path: str,
    document_id: str,
    original_filename: str,
    user_id: str,
):
    """
    Background document processing.

    The user_id is passed all the way into
    index_document.py so every Qdrant chunk
    receives ownership metadata.
    """

    try:

        print()
        print("=" * 60)

        print(
            f"Starting background processing: "
            f"{original_filename}"
        )

        print(
            f"Document ID: "
            f"{document_id}"
        )

        print(
            f"User ID: "
            f"{user_id}"
        )

        print("=" * 60)

        # ----------------------------------------------------
        # Processing status
        # ----------------------------------------------------

        document_status[
            document_id
        ] = {
            "status": "processing",
            "document_id": document_id,
            "filename": original_filename,
            "user_id": user_id,
        }

        # ----------------------------------------------------
        # Reuse already loaded services
        # ----------------------------------------------------

        embedding_service = None
        hybrid_search_service = None

        if rag_service is not None:

            embedding_service = (
                rag_service.embedding_service
            )

            hybrid_search_service = (
                rag_service.hybrid_search
            )

        # ----------------------------------------------------
        # Process document
        # ----------------------------------------------------

        result = process_document(
            pdf_path=file_path,
            document_id=document_id,
            embedding_service=embedding_service,
            hybrid_search_service=hybrid_search_service,
            original_filename=original_filename,
            user_id=user_id,
        )

        # ----------------------------------------------------
        # Mark completed
        # ----------------------------------------------------

        document_status[
            document_id
        ] = {
            "status": "completed",
            "document_id": document_id,
            "filename": original_filename,
            "user_id": user_id,
            "page_count": result[
                "page_count"
            ],
            "chunk_count": result[
                "chunk_count"
            ],
            "embedding_dimension": result[
                "embedding_dimension"
            ],
        }

        print()
        print(
            f"Document processing completed: "
            f"{original_filename}"
        )

        print(
            f"Owner: {user_id}"
        )

    except Exception as exc:

        print()
        print(
            f"Document processing failed: "
            f"{original_filename}"
        )

        print(
            f"User: {user_id}"
        )

        print(
            f"Error: {exc}"
        )

        document_status[
            document_id
        ] = {
            "status": "failed",
            "document_id": document_id,
            "filename": original_filename,
            "user_id": user_id,
            "error": str(exc),
        }


# ============================================================
# Upload Document
# ============================================================

@app.post("/documents/upload")
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Header(
        default=None,
        alias="X-User-ID",
    ),
):

    # --------------------------------------------------------
    # Validate user
    # --------------------------------------------------------

    if not user_id or not user_id.strip():

        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required."
            ),
        )

    user_id = user_id.strip()

    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    original_filename = file.filename

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF files are supported."
            ),
        )

    # --------------------------------------------------------
    # Generate unique document ID
    # --------------------------------------------------------

    document_id = str(
        uuid.uuid4()
    )

    # Physical file remains UUID-based
    # to prevent filename collisions.

    stored_filename = (
        f"{document_id}{extension}"
    )

    file_path = (
        UPLOAD_DIR
        / stored_filename
    )

    # --------------------------------------------------------
    # Save uploaded PDF
    # --------------------------------------------------------

    try:

        with open(
            file_path,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save uploaded "
                f"file: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Initial status
    # --------------------------------------------------------

    document_status[
        document_id
    ] = {
        "status": "queued",
        "document_id": document_id,
        "filename": original_filename,
        "user_id": user_id,
    }

    # --------------------------------------------------------
    # Background processing
    # --------------------------------------------------------

    background_tasks.add_task(
        process_uploaded_document,
        str(file_path),
        document_id,
        original_filename,
        user_id,
    )

    # --------------------------------------------------------
    # Immediate response
    # --------------------------------------------------------

    return {
        "status": "processing",
        "message": (
            "Document uploaded successfully. "
            "Processing has started in the background."
        ),
        "document_id": document_id,
        "filename": original_filename,
        "stored_filename": stored_filename,
    }


# ============================================================
# Document Processing Status
# ============================================================

@app.get(
    "/documents/{document_id}/status"
)
def get_document_status(
    document_id: str,
    user_id: str = Header(
        default=None,
        alias="X-User-ID",
    ),
):

    # --------------------------------------------------------
    # Validate user
    # --------------------------------------------------------

    if not user_id or not user_id.strip():

        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required."
            ),
        )

    user_id = user_id.strip()

    # --------------------------------------------------------
    # Find status
    # --------------------------------------------------------

    status = document_status.get(
        document_id
    )

    if status is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Document processing "
                "status not found."
            ),
        )

    # --------------------------------------------------------
    # Ownership check
    # --------------------------------------------------------

    if status.get(
        "user_id"
    ) != user_id:

        raise HTTPException(
            status_code=404,
            detail=(
                "Document not found."
            ),
        )

    return status


# ============================================================
# List Documents
# ============================================================

@app.get("/documents")
def get_documents(
    user_id: str = Header(
        default=None,
        alias="X-User-ID",
    ),
):

    # --------------------------------------------------------
    # Validate user
    # --------------------------------------------------------

    if not user_id or not user_id.strip():

        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required."
            ),
        )

    user_id = user_id.strip()

    # --------------------------------------------------------
    # RAG service
    # --------------------------------------------------------

    if rag_service is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "RAG service is not ready."
            ),
        )

    try:

        vector_store = (
            rag_service
            .hybrid_search
            .vector_store
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Only retrieve points belonging
        # to this user.
        # ----------------------------------------------------

        points = (
            vector_store.get_all_points(
                collection_name=COLLECTION_NAME,
                user_id=user_id,
            )
        )

        documents = {}

        for point in points:

            payload = (
                point.payload or {}
            )

            document_id = (
                payload.get(
                    "document_id"
                )
            )

            if not document_id:
                continue

            # ------------------------------------------------
            # Defensive ownership check
            # ------------------------------------------------

            if (
                payload.get("user_id")
                != user_id
            ):
                continue

            if (
                document_id
                not in documents
            ):

                documents[
                    document_id
                ] = {
                    "document_id":
                        document_id,

                    "filename":
                        payload.get(
                            "filename",
                            "Unknown document",
                        ),

                    "chunk_count":
                        0,

                    "pages":
                        set(),
                }

            documents[
                document_id
            ]["chunk_count"] += 1

            page_number = (
                payload.get(
                    "page_number"
                )
            )

            if page_number is not None:

                documents[
                    document_id
                ]["pages"].add(
                    page_number
                )

        # ----------------------------------------------------
        # Build response
        # ----------------------------------------------------

        result = []

        for document in (
            documents.values()
        ):

            result.append(
                {
                    "document_id":
                        document[
                            "document_id"
                        ],

                    "filename":
                        document[
                            "filename"
                        ],

                    "page_count":
                        len(
                            document[
                                "pages"
                            ]
                        ),

                    "chunk_count":
                        document[
                            "chunk_count"
                        ],
                }
            )

        result.sort(
            key=lambda item:
                (
                    item[
                        "filename"
                    ]
                    or ""
                ).lower()
        )

        return {
            "count": len(result),
            "documents": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to retrieve "
                f"documents: {exc}"
            ),
        )


# ============================================================
# DELETE DOCUMENT
# ============================================================

@app.delete(
    "/documents/{document_id}"
)
def delete_document(
    document_id: str,
    user_id: str = Header(
        default=None,
        alias="X-User-ID",
    ),
):

    # --------------------------------------------------------
    # Validate user
    # --------------------------------------------------------

    if not user_id or not user_id.strip():

        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required."
            ),
        )

    user_id = user_id.strip()

    # --------------------------------------------------------
    # RAG service
    # --------------------------------------------------------

    if rag_service is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "RAG service is not ready."
            ),
        )

    vector_store = (
        rag_service
        .hybrid_search
        .vector_store
    )

    # --------------------------------------------------------
    # Check document ownership
    # --------------------------------------------------------

    try:

        exists = (
            vector_store.document_exists(
                collection_name=COLLECTION_NAME,
                document_id=document_id,
                user_id=user_id,
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to check "
                f"document: {exc}"
            ),
        )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Return 404 instead of revealing that another
    # user owns the document.
    # --------------------------------------------------------

    if not exists:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # --------------------------------------------------------
    # Find original filename
    # --------------------------------------------------------

    original_filename = None

    try:

        points = (
            vector_store.get_all_points(
                collection_name=COLLECTION_NAME,
                user_id=user_id,
            )
        )

        for point in points:

            payload = (
                point.payload or {}
            )

            if (
                payload.get(
                    "document_id"
                )
                == document_id
                and payload.get(
                    "user_id"
                )
                == user_id
            ):

                original_filename = (
                    payload.get(
                        "filename"
                    )
                )

                break

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to retrieve "
                f"document metadata: "
                f"{exc}"
            ),
        )

    # --------------------------------------------------------
    # Delete vectors
    # --------------------------------------------------------

    try:

        deleted_chunks = (
            vector_store.delete_document(
                collection_name=COLLECTION_NAME,
                document_id=document_id,
                user_id=user_id,
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to delete document "
                f"from Qdrant: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Delete physical PDF
    # --------------------------------------------------------

    deleted_file = False

    pdf_file = (
        UPLOAD_DIR
        / f"{document_id}.pdf"
    )

    if pdf_file.exists():

        try:

            pdf_file.unlink()

            deleted_file = True

        except Exception as exc:

            print(
                "Warning: failed to delete "
                f"uploaded PDF: {exc}"
            )

    # --------------------------------------------------------
    # Remove processing status
    # --------------------------------------------------------

    document_status.pop(
        document_id,
        None,
    )

    # --------------------------------------------------------
    # Refresh BM25
    # --------------------------------------------------------

    try:

        rag_service.hybrid_search.refresh_bm25_index()

    except Exception as exc:

        print(
            "Warning: BM25 refresh failed: "
            f"{exc}"
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "status": "success",

        "message": (
            "Document deleted successfully."
        ),

        "document_id":
            document_id,

        "filename":
            original_filename,

        "deleted_chunks":
            deleted_chunks,

        "deleted_file":
            deleted_file,
    }


# ============================================================
# Ask Question
# ============================================================

@app.post("/ask")
def ask_question(
    request: AskRequest,
    user_id: str = Header(
        default=None,
        alias="X-User-ID",
    ),
):

    # --------------------------------------------------------
    # Validate user
    # --------------------------------------------------------

    if not user_id or not user_id.strip():

        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required."
            ),
        )

    user_id = user_id.strip()

    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )

    # --------------------------------------------------------
    # RAG service
    # --------------------------------------------------------

    if rag_service is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "RAG service is not ready."
            ),
        )

    # --------------------------------------------------------
    # Validate document ownership
    # --------------------------------------------------------

    if request.document_id:

        vector_store = (
            rag_service
            .hybrid_search
            .vector_store
        )

        try:

            exists = (
                vector_store.document_exists(
                    collection_name=COLLECTION_NAME,
                    document_id=(
                        request.document_id
                    ),
                    user_id=user_id,
                )
            )

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Failed to check "
                    f"document: {exc}"
                ),
            )

        # ----------------------------------------------------
        # Do not reveal whether another user owns
        # this document.
        # ----------------------------------------------------

        if not exists:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Document not found."
                ),
            )

    # --------------------------------------------------------
    # Execute RAG
    # --------------------------------------------------------

    try:

        result = rag_service.ask(
            query=request.question,

            user_id=user_id,

            document_id=(
                request.document_id
            ),

            retrieval_limit=5,

            rerank_limit=5,

            relevance_threshold=0.10,

            max_context_documents=2,
        )

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
                "Failed to process "
                "the question."
            ),
        )

    # --------------------------------------------------------
    # Sources
    # --------------------------------------------------------

    sources = []

    for source in (
        result["sources"]
    ):

        sources.append(
            {
                "document_id":
                    source.get(
                        "document_id"
                    ),

                "filename":
                    source["filename"],

                "page":
                    source["page_number"],

                "chunk":
                    source["chunk_index"],

                "reranker_score":
                    source[
                        "reranker_score"
                    ],
            }
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "question":
            result["query"],

        "document_id":
            request.document_id,

        "answer":
            result["answer"],

        "sources":
            sources,
    }