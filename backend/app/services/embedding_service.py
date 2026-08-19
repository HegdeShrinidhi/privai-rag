from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self):
        self.model_name = "BAAI/bge-m3"

        print(f"Loading embedding model: {self.model_name}")

        self.model = SentenceTransformer(
            self.model_name
        )

        print("Embedding model loaded successfully.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Convert document chunks into embedding vectors.
        """

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Convert a user query into an embedding vector.
        """

        embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        )

        return embedding.tolist()