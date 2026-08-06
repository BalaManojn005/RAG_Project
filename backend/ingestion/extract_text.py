import fitz  # PyMuPDF
from docx import Document
from pathlib import Path


def extract_pdf(file_path):
    """
    Extract text from a PDF document.
    """

    text = ""

    pdf = fitz.open(file_path)

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text


def extract_docx(file_path):
    """
    Extract text from a DOCX document.
    """

    document = Document(file_path)

    text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )

    return text


def extract_txt(file_path):
    """
    Extract text from a TXT document.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_text(file_path):
    """
    Automatically detect the file type
    and call the correct extraction function.
    """

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_pdf(file_path)

    elif extension == ".docx":
        return extract_docx(file_path)

    elif extension == ".txt":
        return extract_txt(file_path)

    else:
        raise ValueError(f"Unsupported file type: {extension}")