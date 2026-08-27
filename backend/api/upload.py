from pathlib import Path

from fastapi import APIRouter, HTTPException, File, UploadFile

from backend.rag.rag_pipeline import ingest_document


router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF and build its FAISS index."""

    filename = Path(file.filename or "").name

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="A PDF file is required.",
        )

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF documents are supported.",
        )

    file_path = UPLOAD_DIR / filename

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())

        result = ingest_document(str(file_path))

        return {
            "message": result.get(
                "message",
                "Document indexed successfully.",
            ),
            "chunks": result.get("chunks", 0),
            "filename": filename,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {exc}",
        ) from exc
