from sentence_transformers import SentenceTransformer

# Load the embedding model only once
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(chunks: list[str]):
    """
    Generate embeddings for a list of text chunks.
    """

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True
    )

    return embeddings