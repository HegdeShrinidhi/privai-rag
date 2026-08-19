from app.services.vector_store import VectorStore


COLLECTION_NAME = "privai_documents"

vector_store = VectorStore()

vector_store.create_collection(
    collection_name=COLLECTION_NAME,
    vector_size=1024,
)

print(
    "Collection exists:",
    vector_store.collection_exists(COLLECTION_NAME),
)