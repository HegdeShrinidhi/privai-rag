from app.services.rag_service import RAGService


def main():

    query = (
        "How many days of annual leave "
        "do employees receive?"
    )

    rag = RAGService()

    result = rag.ask(
        query=query,
        retrieval_limit=5,
        rerank_limit=5,
        relevance_threshold=0.10,
        max_context_documents=2,
    )

    print("\n" + "=" * 70)
    print("RAG ANSWER")
    print("=" * 70)

    print(result["answer"])

    print("\n" + "=" * 70)
    print("SOURCES")
    print("=" * 70)

    for index, source in enumerate(
        result["sources"],
        start=1,
    ):
        print(
            f"\n[{index}] "
            f"{source['filename']} "
            f"| Page {source['page_number']} "
            f"| Chunk {source['chunk_index']} "
            f"| Reranker "
            f"{source['reranker_score']:.4f}"
        )

    print("\n" + "=" * 70)
    print("CONTEXT USED BY LLM")
    print("=" * 70)

    for document in result["context_documents"]:
        print(
            f"\nPage {document['page_number']} "
            f"| Chunk {document['chunk_index']}"
        )
        print(document["text"])


if __name__ == "__main__":
    main()