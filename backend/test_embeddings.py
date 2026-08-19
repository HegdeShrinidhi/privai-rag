from app.services.embedding_service import EmbeddingService


embedding_service = EmbeddingService()

text = "Employees receive 24 days of paid annual leave per year."

embedding = embedding_service.embed_query(text)

print("Embedding dimension:", len(embedding))
print("First 10 values:", embedding[:10])