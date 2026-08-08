from backend.ingestion.hts_indexer import build_hts_index


if __name__ == "__main__":

    build_hts_index(
        file_path="data/hts/hts_2026_revision_12.json",
        output_dir="data/hts/index",
    )