MODEL_NAME = "all-MiniLM-L6-v2"
model = None


def get_model():
    """Load the embedding model on first use, not while the API imports."""
    global model

    if model is None:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(MODEL_NAME)

    return model


def generate_embeddings(chunks: list[str]):
    """
    Generate embeddings for a list of text chunks.
    """

    embeddings = get_model().encode(
        chunks,
        convert_to_numpy=True
    )

    return embeddings
