from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


COLLECTION_NAME = "privai_documents"


def search_documents(query: str):
    embedding_service = EmbeddingService()

    query_vector = embedding_service.embed_query(query)

    vector_store = VectorStore()

    results = vector_store.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=3,
    )

    print("\nSearch Query:")
    print(query)

    print("\nResults:")

    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print(f"Score: {result.score}")
        print(f"Document: {result.payload['filename']}")
        print(f"Page: {result.payload['page_number']}")
        print(f"Chunk: {result.payload['chunk_index']}")
        print(f"Text: {result.payload['text']}")


if __name__ == "__main__":
    search_documents(
        "How many days of annual leave do employees receive?"
    )