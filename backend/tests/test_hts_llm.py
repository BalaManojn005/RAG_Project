from backend.retrieval.hts_retriever import search_hts
from backend.llm.llm_client import generate_answer


def build_hts_context(results):
    """
    Convert retrieved HTS records into grounded
    context for the LLM.
    """

    context_parts = []

    for i, result in enumerate(results, 1):

        context_parts.append(
            f"""
HTS RESULT {i}

HTS Number:
{result["htsno"]}

Description:
{result["description"]}

General Rate:
{result["general"]}

Special Rate:
{result["special"]}

Other:
{result["other"]}

Units:
{result["units"]}

Footnotes:
{result["footnotes"]}

Source Text:
{result["text"]}
""".strip()
        )

    return "\n\n".join(context_parts)


def ask_hts_question(question):
    """
    Retrieve HTS information and generate a
    grounded answer.
    """

    results = search_hts(
        question,
        top_k=5
    )

    if not results:
        return (
            "I could not find relevant HTS information "
            "in the indexed data."
        )

    context = build_hts_context(
        results
    )

    system_instruction = """
You are an HTS tariff information assistant.

Answer ONLY using the supplied HTS context.

Rules:
1. Do not invent HTS numbers.
2. Do not invent tariff rates.
3. Do not invent duty information.
4. Do not use outside knowledge.
5. If the context does not contain enough information,
   clearly say that the indexed HTS data does not
   provide enough information.
6. When an exact HTS number is present, use it directly.
7. Keep the answer clear and concise.
"""

    prompt = f"""
{system_instruction}

HTS CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    return generate_answer(
        question,
        prompt
    )


if __name__ == "__main__":

    questions = [
        "What is HTS 0101.21.00?",
        "What is the tariff information for live horses?",
        "What HTS information is available for purebred breeding animals?",
    ]

    for question in questions:

        print("\n" + "=" * 70)
        print(f"QUESTION: {question}")
        print("=" * 70)

        answer = ask_hts_question(
            question
        )

        print("\nANSWER:")
        print(answer)