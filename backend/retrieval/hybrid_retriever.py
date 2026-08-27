from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import search

from backend.retrieval.bm25_retriever import (
    create_bm25_index,
    search_bm25,
)


def retrieve_hybrid(
    query,
    index,
    chunks,
    top_k=3
):
    """
    Hybrid retrieval using:

    1. Dense retrieval with FAISS
    2. Sparse retrieval with BM25
    3. Reciprocal Rank Fusion (RRF)

    Returns detailed retrieval results so that
    the RAG pipeline can expose the source chunks.
    """

    if not chunks:
        return []


    # ========================================================
    # 1. DENSE RETRIEVAL
    # ========================================================

    query_embedding = generate_embeddings(
        [query]
    )[0]

    dense_k = min(
        10,
        len(chunks)
    )

    distances, dense_indices = search(
        index,
        query_embedding,
        dense_k
    )

    dense_ranking = [
        int(idx)
        for idx in dense_indices[0]
        if idx != -1
    ]


    # ========================================================
    # 2. SPARSE RETRIEVAL
    # ========================================================

    bm25 = create_bm25_index(
        chunks
    )

    sparse_k = min(
        10,
        len(chunks)
    )

    sparse_indices, sparse_scores = search_bm25(
        bm25,
        query,
        sparse_k
    )


    # ========================================================
    # 3. RECIPROCAL RANK FUSION
    # ========================================================

    rrf_scores = {}

    k = 60


    # Dense ranking

    for rank, idx in enumerate(
        dense_ranking
    ):

        rrf_scores[idx] = (
            rrf_scores.get(
                idx,
                0
            )
            + 1 / (
                k + rank + 1
            )
        )


    # Sparse ranking

    for rank, idx in enumerate(
        sparse_indices
    ):

        rrf_scores[idx] = (
            rrf_scores.get(
                idx,
                0
            )
            + 1 / (
                k + rank + 1
            )
        )


    # ========================================================
    # 4. FINAL RANKING
    # ========================================================

    ranked_indices = sorted(
        rrf_scores,
        key=rrf_scores.get,
        reverse=True
    )[:top_k]


    # ========================================================
    # 5. RETURN DETAILED RESULTS
    # ========================================================

    results = []

    for rank, idx in enumerate(
        ranked_indices,
        start=1
    ):

        results.append(
            {
                "chunk_id": idx,
                "rank": rank,
                "rrf_score": rrf_scores[idx],
                "content": chunks[idx],
            }
        )


    return results