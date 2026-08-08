from backend.retrieval.hts_retriever import search_hts


def print_results(query):
    print("\n" + "=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)

    results = search_hts(
        query,
        top_k=5
    )

    if not results:
        print("\nNo relevant HTS results found.")
        return

    for i, result in enumerate(results, 1):

        print(
            f"\n{i}. HTS: {result['htsno']}"
        )

        print(
            f"   Description: "
            f"{result['description']}"
        )

        print(
            f"   General: "
            f"{result['general']}"
        )

        print(
            f"   Special: "
            f"{result['special']}"
        )

        print(
            f"   Other: "
            f"{result['other']}"
        )

        print(
            f"   Relevance: "
            f"{result['relevance_score']}"
        )


if __name__ == "__main__":

    print_results(
        "What is HTS 0101.21.00?"
    )

    print_results(
        "purebred breeding horses"
    )

    print_results(
        "tariff for live horses"
    )