import re

def clean_text(text: str) -> str:
    """
    Clean extracted text by removing
    unnecessary spaces and blank lines.
    """

    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text