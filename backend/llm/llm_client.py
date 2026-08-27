from ollama import chat


MODEL = "gemma3:4b"


# ============================================================
# NORMAL GENERATION
# ============================================================

def generate_answer(
    question: str,
    context: str
) -> str:
    """
    Generate a complete answer using Ollama.
    """

    prompt = f"""
You are a helpful AI document assistant.

Answer ONLY using the supplied context.

IMPORTANT RULES:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not contained in the context,
   say:

"I couldn't find that information in the document."

4. Answer clearly and directly.
5. If the user asks for a summary, summarize only
   the supplied document context.

Context:
{context}

Question:
{question}

Answer:
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

    return response.message.content


# ============================================================
# TRUE STREAMING GENERATION
# ============================================================

def generate_answer_stream(
    question: str,
    context: str
):
    """
    Generate an answer token-by-token using Ollama.
    """

    prompt = f"""
You are a helpful AI document assistant.

Answer ONLY using the supplied context.

IMPORTANT RULES:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not contained in the context,
   say:

"I couldn't find that information in the document."

4. Answer clearly and directly.
5. If the user asks for a summary, summarize only
   the supplied document context.

Context:
{context}

Question:
{question}

Answer:
"""

    stream = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        stream=True,
    )

    for chunk in stream:

        if not chunk:
            continue

        try:

            token = chunk.message.content

        except AttributeError:

            token = ""

        if token:
            yield token