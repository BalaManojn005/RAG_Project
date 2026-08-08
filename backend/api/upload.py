from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from backend.rag.rag_pipeline import ingest_document

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF and build its FAISS index.
    """

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    message = ingest_document(str(file_path))

    return {
        "message": message,
        "filename": file.filename
    }