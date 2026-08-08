import json
import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi


def build_hts_bm25_index(
    texts_path="data/hts/index/texts.json",
    output_path="data/hts/index/bm25.pkl",
):
    """
    Build and persist a BM25 index using the same
    text ordering as the HTS FAISS index.
    """

    texts_path = Path(texts_path)
    output_path = Path(output_path)

    if not texts_path.exists():
        raise FileNotFoundError(
            f"Texts file not found: {texts_path}"
        )

    print("Loading HTS texts...")

    with texts_path.open(
        "r",
        encoding="utf-8"
    ) as file:
        texts = json.load(file)

    print(f"Loaded {len(texts)} HTS texts.")

    print("Tokenizing HTS texts...")

    tokenized_texts = [
        text.lower().split()
        for text in texts
    ]

    print("Building BM25 index...")

    bm25 = BM25Okapi(tokenized_texts)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open("wb") as file:
        pickle.dump(bm25, file)

    print("\n========== BM25 INDEX COMPLETE ==========")

    print(f"Documents: {len(texts)}")
    print(f"BM25 index: {output_path}")

    return bm25