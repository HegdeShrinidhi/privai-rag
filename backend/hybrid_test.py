from app.services.hybrid_search import HybridSearchService


def main():

    query = (
        "How many days of annual leave "
        "do employees receive?"
    )

    service = HybridSearchService()

    results = service.search(
        query=query,
        limit=5,
        vector_weight=0.6,
        bm25_weight=0.4,
    )

    print("\nHybrid Search Query:")
    print(query)

    print("\nHybrid Results:")

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\n--- Result {index} ---"
        )

        print(
            f"Hybrid Score: "
            f"{result['hybrid_score']:.4f}"
        )

        print(
            f"Vector Score: "
            f"{result['vector_score']:.4f}"
        )

        print(
            f"BM25 Score: "
            f"{result['bm25_score']:.4f}"
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