import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "privai_documents"

print("=" * 60)
print("Connecting to Qdrant Cloud...")
print("=" * 60)

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60,
)

print("Connected.")

# ---------------------------------------------------------
# Create user_id index
# ---------------------------------------------------------

print("\nCreating user_id index...")

client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="user_id",
    field_schema=PayloadSchemaType.KEYWORD,
)

print("user_id index created successfully.")

# ---------------------------------------------------------
# Create document_id index
# ---------------------------------------------------------

print("\nCreating document_id index...")

client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="document_id",
    field_schema=PayloadSchemaType.KEYWORD,
)

print("document_id index created successfully.")

# ---------------------------------------------------------
# Show collection information
# ---------------------------------------------------------

print("\nChecking collection...")

collection_info = client.get_collection(
    COLLECTION_NAME
)

print(
    f"Collection: {COLLECTION_NAME}"
)

print(
    f"Points: {collection_info.points_count}"
)

print("\nQdrant indexes configured successfully.")