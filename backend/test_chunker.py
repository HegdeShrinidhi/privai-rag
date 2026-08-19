from app.services.pdf_parser import extract_text_from_pdf
from app.services.text_cleaner import clean_text
from app.services.chunker import create_chunks


PDF_PATH = "uploads/privai_rag_employee_policy_handbook.pdf"

document = extract_text_from_pdf(PDF_PATH)

print(f"Pages found: {len(document['pages'])}")

for page in document["pages"]:
    print(f"\nProcessing page {page['page_number']}...")

    cleaned_text = clean_text(page["text"])

    chunks = create_chunks(cleaned_text)

    print(f"Chunks on page: {len(chunks)}")

    for index, chunk in enumerate(chunks):
        print("\n" + "=" * 60)
        print(f"Page {page['page_number']} | Chunk {index}")
        print("=" * 60)
        print(chunk)

print("\nChunking test completed.")