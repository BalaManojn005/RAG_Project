from backend.ingestion.extract_text import extract_text
from backend.ingestion.text_checker import has_text
from backend.processing.clean_text import clean_text
from backend.processing.chunk_text import chunk_text


def process_document(file_path: str):
    """
    Complete preprocessing pipeline.
    """

    text = extract_text(file_path)

    if not has_text(text):
        return {
            "status": "ocr_required",
            "message": "No readable text found. OCR is required."
        }

    cleaned_text = clean_text(text)
    chunks = chunk_text(cleaned_text)

    return {
        "status": "success",
        "chunks": chunks
    }