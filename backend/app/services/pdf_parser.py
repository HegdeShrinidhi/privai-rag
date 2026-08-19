from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract text from a PDF document.

    Returns:
        dict containing page count and extracted page text.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    reader = PdfReader(str(path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append(
            {
                "page_number": page_number,
                "text": text,
            }
        )

    return {
        "filename": path.name,
        "page_count": len(reader.pages),
        "pages": pages,
    }