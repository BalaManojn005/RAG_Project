def classify_intent(question: str) -> str:
    q = question.lower().strip()

    summary_words = [
        "summary",
        "summarize",
        "summarise",
        "overview",
        "what is this document about",
        "what does this document contain",
    ]

    for word in summary_words:
        if word in q:
            return "summary"

    return "question"