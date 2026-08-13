from backend.intent.handler import prepare_question
from backend.processing.pipeline import process_document
from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import create_index

from backend.retrieval.hybrid_retriever import retrieve_hybrid
from backend.retrieval.hts_retriever import search_hts

from backend.llm.llm_client import generate_answer

from backend.storage.storage import (
    save_index,
    load_index,
    save_chunks,
    load_chunks,
)


# ============================================================
# DOCUMENT INGESTION
# ============================================================

def ingest_document(file_path):
    """
    Process a document and create its FAISS index.
    """

    result = process_document(file_path)

    chunks = result["chunks"]

    # Generate dense embeddings
    embeddings = generate_embeddings(chunks)

    # Create FAISS index
    index = create_index(embeddings)

    # Save index and chunks
    save_index(index)
    save_chunks(chunks)

    return "Document indexed successfully."


# ============================================================
# HTS QUESTION DETECTION
# ============================================================

def is_hts_question(question):
    """
    Detect whether the question is related to
    HTS / tariff classification.
    """

    question_lower = question.lower()

    hts_keywords = [
        "hts",
        "hts code",
        "hts number",
        "harmonized tariff",
        "tariff",
        "tariff information",
        "tariff code",
        "tariff number",
        "tariff rate",
        "customs duty",
        "customs tariff",
        "import duty",
        "import tariff",
    ]

    # Direct HTS code pattern
    import re

    if re.search(
        r"\b\d{4}(?:\.\d{2}){0,3}\b",
        question
    ):
        return True

    # Keyword detection
    for keyword in hts_keywords:
        if keyword in question_lower:
            return True

    return False


# ============================================================
# HTS CONTEXT
# ============================================================

def build_hts_context(results):
    """
    Convert HTS retrieval results into
    grounded LLM context.
    """

    context_parts = []

    for i, result in enumerate(results, 1):

        context_parts.append(
            f"""
HTS RESULT {i}

HTS Number:
{result.get("htsno", "")}

Description:
{result.get("description", "")}

General Rate:
{result.get("general", "")}

Special Rate:
{result.get("special", "")}

Other:
{result.get("other", "")}

Units:
{result.get("units", [])}

Footnotes:
{result.get("footnotes", [])}

Source Text:
{result.get("text", "")}
""".strip()
        )

    return "\n\n".join(context_parts)


# ============================================================
# HTS QUESTION
# ============================================================

def answer_hts_question(question):
    """
    Retrieve HTS records and generate a grounded answer.
    """

    results = search_hts(
        question,
        top_k=5
    )

    if not results:

        return {
            "answer": (
                "I could not find relevant HTS information "
                "in the indexed HTS data."
            ),
            "sources": []
        }

    context = build_hts_context(results)

    prompt = f"""
You are an HTS tariff information assistant.

Answer the user's question using ONLY the HTS
records provided below.

STRICT RULES:

1. Do not invent HTS numbers.
2. Do not invent tariff rates.
3. Do not invent customs duties.
4. Do not invent units or footnotes.
5. Do not use information outside the supplied context.
6. If the context does not contain enough information,
   clearly say that the indexed HTS data does not
   provide enough information.
7. If an exact HTS number is present, use that exact
   HTS number.
8. If multiple relevant HTS records exist, clearly
   distinguish them.
9. Keep the answer concise and factual.

HTS CONTEXT:

{context}

USER QUESTION:

{question}

ANSWER:
"""

    answer = generate_answer(
        question,
        prompt
    )

    sources = []

    for i, result in enumerate(
        results,
        start=1
    ):
        sources.append(
            {
                "type": "hts",
                "rank": i,
                "hts_number": result.get(
                    "htsno",
                    ""
                ),
                "description": result.get(
                    "description",
                    ""
                ),
            }
        )

    return {
        "answer": answer,
        "sources": sources
    }


# ============================================================
# CONVERSATION HISTORY
# ============================================================

def build_history_context(
    conversation_messages
):
    """
    Convert previous conversation messages into
    context that can be supplied to the LLM.
    """

    if not conversation_messages:
        return ""

    history_lines = []

    # Keep only latest 10 messages
    recent_messages = (
        conversation_messages[-10:]
    )

    for message in recent_messages:

        role = message.get(
            "role",
            ""
        )

        content = message.get(
            "content",
            ""
        )

        if not content:
            continue

        if role == "user":
            role_name = "USER"

        elif role == "assistant":
            role_name = "ASSISTANT"

        else:
            role_name = role.upper()

        history_lines.append(
            f"{role_name}: {content}"
        )

    if not history_lines:
        return ""

    return (
        "\n\nPREVIOUS CONVERSATION:\n"
        + "\n".join(history_lines)
        + "\n\n"
    )


# ============================================================
# BUILD DOCUMENT CONTEXT
# ============================================================

def build_document_context(
    retrieval_results
):
    """
    Convert detailed hybrid retrieval results
    into the plain text context expected by
    the LLM.
    """

    if not retrieval_results:
        return ""

    context_parts = []

    for result in retrieval_results:

        content = result.get(
            "content",
            ""
        )

        if content:
            context_parts.append(
                content
            )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# BUILD SOURCE INFORMATION
# ============================================================

def build_sources(
    retrieval_results
):
    """
    Convert retrieval results into
    frontend-friendly source information.
    """

    sources = []

    for result in retrieval_results:

        sources.append(
            {
                "type": "document",
                "chunk_id": result.get(
                    "chunk_id"
                ),
                "rank": result.get(
                    "rank"
                ),
                "score": result.get(
                    "rrf_score"
                ),
                "content": result.get(
                    "content",
                    ""
                ),
            }
        )

    return sources


# ============================================================
# MAIN QUESTION ROUTER
# ============================================================

def ask_question(
    question,
    conversation_messages=None
):
    """
    Main RAG question router.

    HTS questions:
        HTS Retriever → grounded LLM

    Normal document questions:
        Intent → Hybrid Retriever → LLM

    Conversation history:
        Previous messages → LLM context

    Returns:
        {
            "answer": str,
            "sources": list
        }
    """

    conversation_messages = (
        conversation_messages or []
    )

    history_context = (
        build_history_context(
            conversation_messages
        )
    )


    # ========================================================
    # HTS ROUTE
    # ========================================================

    if is_hts_question(question):

        return answer_hts_question(
            question
        )


    # ========================================================
    # NORMAL DOCUMENT RAG ROUTE
    # ========================================================

    index = load_index()

    chunks = load_chunks()


    # ========================================================
    # INTENT DETECTION
    # ========================================================

    prepared = prepare_question(
        question
    )


    # ========================================================
    # HYBRID RETRIEVAL
    # ========================================================

    retrieval_results = retrieve_hybrid(
        prepared["query"],
        index,
        chunks,
        top_k=3
    )


    # ========================================================
    # NO RETRIEVAL RESULTS
    # ========================================================

    if not retrieval_results:

        return {
            "answer": (
                "I couldn't find that information "
                "in the document."
            ),
            "sources": []
        }


    # ========================================================
    # BUILD LLM CONTEXT
    # ========================================================

    document_context = (
        build_document_context(
            retrieval_results
        )
    )


    # ========================================================
    # BUILD SOURCES
    # ========================================================

    sources = build_sources(
        retrieval_results
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    if prepared["intent"] == "summary":

        summary_prompt = (
            "Summarize the following document content. "
            "Include the main topics and important points. "
            "Do not invent information.\n\n"
            + document_context
            + history_context
        )

        answer = generate_answer(
            "Summarize the document.",
            summary_prompt
        )

        return {
            "answer": answer,
            "sources": sources
        }


    # ========================================================
    # NORMAL QUESTION
    # ========================================================

    normal_prompt = (
        document_context
        + history_context
    )

    answer = generate_answer(
        question,
        normal_prompt
    )


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "answer": answer,
        "sources": sources
    }