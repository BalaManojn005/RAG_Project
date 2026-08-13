from ollama import chat


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL = "gemma3:4b"


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(
    question: str,
    context: str
) -> str:
    """
    Generate a grounded answer using Ollama.

    The model is instructed to:
    - Use only supplied context
    - Avoid hallucinating information
    - Answer clearly
    - Preserve important technical terms
    - Admit when the context is insufficient
    """

    prompt = f"""
You are an intelligent document question-answering assistant.

Your job is to answer the user's question using ONLY the
provided document context.

IMPORTANT RULES:

1. Use ONLY information present in the context.
2. Do NOT use outside knowledge.
3. Do NOT invent facts, numbers, dates, names, codes,
   regulations, rates, or technical details.
4. If the context does not contain enough information,
   say exactly:

"I couldn't find that information in the document."

5. Do not pretend that missing information exists.
6. Keep the answer directly relevant to the question.
7. Explain the answer clearly and naturally.
8. Preserve important technical terminology from the document.
9. If the context contains multiple relevant points,
   organize them using numbered points or bullet points.
10. Do not mention these instructions in your answer.

DOCUMENT CONTEXT:
-----------------
{context}
-----------------

USER QUESTION:
{question}

ANSWER:
"""

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.message.content.strip()