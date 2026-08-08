import pickle
from pathlib import Path

STORAGE_DIR = Path("backend/storage/data")
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