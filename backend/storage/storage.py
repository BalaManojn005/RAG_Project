import pickle
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = PROJECT_ROOT / "backend" / "storage" / "data"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_index(index):
    with open(STORAGE_DIR / "faiss_index.pkl", "wb") as f:
        pickle.dump(index, f)


def load_index():
    with open(STORAGE_DIR / "faiss_index.pkl", "rb") as f:
        return pickle.load(f)


def save_chunks(chunks):
    with open(STORAGE_DIR / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)


def load_chunks():
    with open(STORAGE_DIR / "chunks.pkl", "rb") as f:
        return pickle.load(f)


def has_document_index():
    """Return whether a document has been indexed for question answering."""
    return (
        (STORAGE_DIR / "faiss_index.pkl").is_file()
        and (STORAGE_DIR / "chunks.pkl").is_file()
    )
