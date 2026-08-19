from pathlib import Path
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.pdf_parser import extract_text_from_pdf
from app.services.text_cleaner import clean_text
from app.services.chunker import create_chunks


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, extract its text, clean it, and create chunks.
    """

    # 1. Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    # 2. Save uploaded PDF
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 3. Extract text
        document = extract_text_from_pdf(str(file_path))

        # 4. Clean page text
        cleaned_pages = []

        for page in document["pages"]:
            cleaned_text = clean_text(page["text"])

            cleaned_pages.append(
                {
                    "page_number": page["page_number"],
                    "text": cleaned_text,
                }
            )

        # 5. Create chunks while preserving page information
        chunks = []

        for page in cleaned_pages:
            page_chunks = create_chunks(page["text"])

            for chunk_index, chunk in enumerate(page_chunks):
                chunks.append(
    {
        "chunk_id": f"{file.filename}-p{page['page_number']}-c{chunk_index}",
        "document_id": file.filename,
        "filename": file.filename,
        "page_number": page["page_number"],
        "chunk_index": chunk_index,
        "text": chunk,
    }
)

        return {
            "filename": document["filename"],
            "page_count": document["page_count"],
            "chunk_count": len(chunks),
            "status": "processed",
            "chunks": chunks,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(exc)}",
        )