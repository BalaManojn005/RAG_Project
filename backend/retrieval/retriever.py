from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import search


def retrieve(query, index, chunks, top_k=3):
    """
    Retrieve the most relevant chunks for a query.
    """

    query_embedding = generate_embeddings([query])[0]

    distances, indices = search(index, query_embedding, top_k)

    results = []

    for idx in indices[0]:
        if idx != -1:
            results.append(chunks[idx])

    return results