from FlagEmbedding import FlagReranker


class RerankerService:
    """
    BGE cross-encoder reranker.

    Takes a query and retrieved document chunks,
    then scores how relevant each chunk is to the query.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
    ):
        print(
            f"Loading reranker model: {model_name}"
        )

        self.reranker = FlagReranker(
            model_name,
            use_fp16=False,
        )

        print(
            "Reranker model loaded successfully."
        )

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Rerank retrieved documents according to
        query-document relevance.
        """

        if not documents:
            return []

        pairs = [
            [
                query,
                document["text"],
            ]
            for document in documents
        ]

        scores = self.reranker.compute_score(
            pairs,
            normalize=True,
        )

        # If only one document is supplied,
        # FlagEmbedding can return a single float.
        if isinstance(scores, float):
            scores = [scores]

        results = []

        for document, score in zip(
            documents,
            scores,
        ):
            result = dict(document)

            result["reranker_score"] = float(
                score
            )

            results.append(result)

        results.sort(
            key=lambda result: result[
                "reranker_score"
            ],
            reverse=True,
        )

        return results[:top_k]