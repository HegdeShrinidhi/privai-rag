from app.services.bm25_service import BM25Service
from app.services.document_store import DocumentStore


COLLECTION_NAME = "privai_documents"


def main():

    # ---------------------------------------------------------
    # 1. Get chunks from Qdrant
    # ---------------------------------------------------------

    document_store = DocumentStore()

    documents = document_store.get_all_chunks(
        COLLECTION_NAME
    )

    print(
        f"Loaded {len(documents)} chunks from Qdrant."
    )

    # ---------------------------------------------------------
    # 2. Build BM25 index
    # ---------------------------------------------------------

    bm25 = BM25Service()

    bm25.build_index(
        documents
    )

    # ---------------------------------------------------------
    # 3. Search
    # ---------------------------------------------------------

    query = (
        "How many days of annual leave "
        "do employees receive?"
    )

    results = bm25.search(
        query=query,
        limit=3,
    )

    print("\nSearch Query:")
    print(query)

    print("\nBM25 Results:")

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\n--- Result {index} ---"
        )

        print(
            f"Score: {result['score']}"
        )

        print(
            f"Document: "
            f"{result['filename']}"
        )

        print(
            f"Page: "
            f"{result['page_number']}"
        )

        print(
            f"Chunk: "
            f"{result['chunk_index']}"
        )

        print(
            f"Text: "
            f"{result['text']}"
        )


if __name__ == "__main__":
    main()