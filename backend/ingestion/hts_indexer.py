import json
from pathlib import Path

import faiss
import numpy as np

from backend.ingestion.hts_parser import (
    parse_hts_file,
    hts_record_to_text,
)
from backend.embeddings.embed_text import generate_embeddings


BATCH_SIZE = 256


def build_hts_index(
    file_path="data/hts/hts_2026_revision_12.json",
    output_dir="data/hts/index",
):
    """
    Build a FAISS index for the complete HTS dataset.

    Records are embedded in batches to reduce memory usage.
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("Loading HTS dataset...")

    records = parse_hts_file(file_path)

    print(f"Loaded {len(records)} HTS records.")

    # --------------------------------------------------
    # Convert HTS records into searchable text
    # --------------------------------------------------

    texts = [
        hts_record_to_text(record)
        for record in records
    ]

    # --------------------------------------------------
    # Generate embeddings in batches
    # --------------------------------------------------

    faiss_index = None

    total = len(texts)

    for start in range(0, total, BATCH_SIZE):

        end = min(start + BATCH_SIZE, total)

        batch = texts[start:end]

        print(
            f"Embedding records "
            f"{start + 1}-{end} / {total}"
        )

        embeddings = generate_embeddings(batch)

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        # Create the FAISS index using the first batch
        if faiss_index is None:

            dimension = embeddings.shape[1]

            faiss_index = faiss.IndexFlatL2(
                dimension
            )

        faiss_index.add(embeddings)

    # --------------------------------------------------
    # Save FAISS index
    # --------------------------------------------------

    faiss_path = output_path / "hts.faiss"

    faiss.write_index(
        faiss_index,
        str(faiss_path)
    )

    # --------------------------------------------------
    # Save normalized records
    # --------------------------------------------------

    records_path = output_path / "records.json"

    with records_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2
        )

    # --------------------------------------------------
    # Save searchable text
    # --------------------------------------------------

    texts_path = output_path / "texts.json"

    with texts_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            texts,
            file,
            ensure_ascii=False
        )

    print("\n========== HTS INDEX COMPLETE ==========")

    print(f"Records: {len(records)}")
    print(f"FAISS vectors: {faiss_index.ntotal}")
    print(f"FAISS index: {faiss_path}")
    print(f"Records file: {records_path}")
    print(f"Texts file: {texts_path}")

    return faiss_index, records, texts