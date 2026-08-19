from app.services.hybrid_search import HybridSearchService
from app.services.reranker import RerankerService


def main():

    query = (
        "How many days of annual leave "
        "do employees receive?"
    )

    # ---------------------------------------------------------
    # 1. Get hybrid retrieval candidates
    # ---------------------------------------------------------

    hybrid_service = HybridSearchService()

    hybrid_results = hybrid_service.search(
        query=query,
        limit=5,
        vector_weight=0.6,
        bm25_weight=0.4,
    )

    print("\nHybrid candidates:")

    for index, result in enumerate(
        hybrid_results,
        start=1,
    ):
        print(
            f"{index}. "
            f"Chunk {result['chunk_index']} "
            f"| Hybrid: "
            f"{result['hybrid_score']:.4f}"
        )

    # ---------------------------------------------------------
    # 2. Rerank candidates
    # ---------------------------------------------------------

    reranker = RerankerService()

    reranked_results = reranker.rerank(
        query=query,
        documents=hybrid_results,
        top_k=5,
    )

    # ---------------------------------------------------------
    # 3. Display reranked results
    # ---------------------------------------------------------

    print("\nReranked Results:")

    for index, result in enumerate(
        reranked_results,
        start=1,
    ):

        print(
            f"\n--- Result {index} ---"
        )

        print(
            f"Reranker Score: "
            f"{result['reranker_score']:.4f}"
        )

        print(
            f"Hybrid Score: "
            f"{result['hybrid_score']:.4f}"
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