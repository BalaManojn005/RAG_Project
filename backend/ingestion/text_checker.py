def has_text(text: str) -> bool:
    """
    Returns True if the extracted text contains
    meaningful content.
    """
    return bool(text and text.strip())