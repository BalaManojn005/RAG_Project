from backend.intent.classifier import classify_intent


def prepare_question(question: str):
    intent = classify_intent(question)

    if intent == "summary":
        return {
            "intent": "summary",
            "query": (
                "main topics important points company quality standards "
                "documentation employee involvement activities and objectives"
            ),
        }

    return {
        "intent": "question",
        "query": question,
    }