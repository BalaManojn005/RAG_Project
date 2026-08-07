import faiss
import numpy as np
from pathlib import Path


def create_index(embeddings):
    """
    Create a FAISS index from embeddings.
    """

    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    return index


def save_index(index, file_path):
    """
    Save FAISS index to disk.
    """

    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, file_path)


def load_index(file_path):
    """
    Load FAISS index from disk.
    """

    return faiss.read_index(file_path)


def search(index, query_embedding, k=3):
    """
    Search for nearest embeddings.
    """

    query_embedding = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_embedding, k)

    return distances, indices