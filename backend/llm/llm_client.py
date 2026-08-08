from ollama import chat

MODEL = "gemma3:4b"


def generate_answer(question: str, context: str) -> str:
    """
    Generate an answer using Ollama.
    """

    prompt = f"""
You are a helpful AI assistant.

Answer ONLY using the context below.

If the answer is not found in the context, reply:

"I couldn't find that information in the document."

Context:
{context}

Question:
{question}
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