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
    has_document_index,
)


# ============================================================
# DOCUMENT INGESTION
# ============================================================

def ingest_document(file_path):
    """
    Process a document, generate embeddings,
    create a FAISS index and save the data.
    """

    result = process_document(file_path)

    chunks = result["chunks"]

    embeddings = generate_embeddings(chunks)

    index = create_index(embeddings)

    save_index(index)
    save_chunks(chunks)

    return {
        "message": "Document indexed successfully.",
        "chunks": len(chunks),
    }


# ============================================================
# HTS QUESTION DETECTION
# ============================================================

def is_hts_question(question):
    """
    Detect whether a question is related to
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

    # --------------------------------------------------------
    # Direct HTS code pattern
    # --------------------------------------------------------

    import re

    if re.search(
        r"\b\d{4}(?:\.\d{2}){0,3}\b",
        question
    ):
        return True

    # --------------------------------------------------------
    # Keyword detection
    # --------------------------------------------------------

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

    for i, result in enumerate(
        results,
        start=1
    ):

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

    return "\n\n".join(
        context_parts
    )


# ============================================================
# HTS SOURCES
# ============================================================

def build_hts_sources(results):
    """
    Convert HTS results into source objects.
    """

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
                "general": result.get(
                    "general",
                    ""
                ),
                "special": result.get(
                    "special",
                    ""
                ),
                "other": result.get(
                    "other",
                    ""
                ),
                "units": result.get(
                    "units",
                    []
                ),
                "footnotes": result.get(
                    "footnotes",
                    []
                ),
            }
        )

    return sources


# ============================================================
# HTS QUESTION
# ============================================================

def answer_hts_question(question):
    """
    Retrieve HTS records and generate
    a grounded answer.
    """

    results = search_hts(
        question,
        top_k=5
    )

    if not results:

        return {
            "answer": (
                "I could not find relevant "
                "HTS information in the "
                "indexed HTS data."
            ),
            "sources": [],
        }

    context = build_hts_context(
        results
    )

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

    sources = build_hts_sources(
        results
    )

    return {
        "answer": answer,
        "sources": sources,
    }


# ============================================================
# DOCUMENT CONTEXT
# ============================================================

def build_document_context(
    results
):
    """
    Convert retrieved document chunks
    into LLM context.
    """

    if not results:
        return ""

    context_parts = []

    for i, result in enumerate(
        results,
        start=1
    ):

        # ----------------------------------------------------
        # Handle dictionary result
        # ----------------------------------------------------

        if isinstance(
            result,
            dict
        ):

            content = result.get(
                "content",
                result.get(
                    "text",
                    ""
                )
            )

        else:

            content = str(result)

        if not content:
            continue

        context_parts.append(
            f"""
DOCUMENT CHUNK {i}

{content}
""".strip()
        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# DOCUMENT SOURCES
# ============================================================

def build_sources(
    results
):
    """
    Convert retrieved document chunks
    into persistent source objects.
    """

    sources = []

    for rank, result in enumerate(
        results,
        start=1
    ):

        if isinstance(
            result,
            dict
        ):

            content = result.get(
                "content",
                result.get(
                    "text",
                    ""
                )
            )

            chunk_id = result.get(
                "chunk_id",
                result.get(
                    "id",
                    rank
                )
            )

            score = result.get(
                "score",
                None
            )

        else:

            content = str(result)
            chunk_id = rank
            score = None

        source = {
            "type": "document",
            "chunk_id": chunk_id,
            "rank": rank,
            "content": content,
        }

        if score is not None:
            source["score"] = score

        sources.append(
            source
        )

    return sources


# ============================================================
# CONVERSATION HISTORY
# ============================================================

def build_history_context(
    conversation_messages
):
    """
    Convert previous conversation messages
    into context for the LLM.
    """

    if not conversation_messages:
        return ""

    history_lines = []

    # Keep latest 10 messages
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

    if is_hts_question(
        question
    ):

        return answer_hts_question(
            question
        )

    # ========================================================
    # DOCUMENT AVAILABILITY
    # ========================================================

    if not has_document_index():

        return {
            "answer": (
                "Upload and index a document "
                "before asking a question."
            ),
            "sources": [],
        }

    # ========================================================
    # LOAD DOCUMENT INDEX
    # ========================================================

    index = load_index()

    chunks = load_chunks()

    if index is None or not chunks:

        return {
            "answer": (
                "Upload and index a document "
                "before asking a question."
            ),
            "sources": [],
        }

    # ========================================================
    # INTENT
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
    # NO RESULTS
    # ========================================================

    if not retrieval_results:

        return {
            "answer": (
                "I couldn't find that "
                "information in the document."
            ),
            "sources": [],
        }

    # ========================================================
    # DOCUMENT CONTEXT
    # ========================================================

    document_context = (
        build_document_context(
            retrieval_results
        )
    )

    # ========================================================
    # SOURCES
    # ========================================================

    sources = build_sources(
        retrieval_results
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    if prepared["intent"] == "summary":

        prompt = (
            "Summarize the following document "
            "content. Include the main topics "
            "and important points. "
            "Do not invent information.\n\n"
            + document_context
            + history_context
        )

        answer = generate_answer(
            "Summarize the document.",
            prompt
        )

        return {
            "answer": answer,
            "sources": sources,
        }

    # ========================================================
    # NORMAL QUESTION
    # ========================================================

    prompt = (
        document_context
        + history_context
    )

    answer = generate_answer(
        question,
        prompt
    )

    return {
        "answer": answer,
        "sources": sources,
    }
    # ============================================================
# STREAMING RAG
# ============================================================

def prepare_streaming_question(
    question,
    conversation_messages=None
):
    """
    Prepare RAG context for true token streaming.

    This function performs retrieval only.
    Ollama generation happens afterwards.
    """

    conversation_messages = (
        conversation_messages or []
    )

    # --------------------------------------------------------
    # HTS
    # --------------------------------------------------------

    if is_hts_question(question):

        results = search_hts(
            question,
            top_k=5
        )

        if not results:

            return {
                "question": question,
                "context": "",
                "sources": [],
            }

        context = build_hts_context(
            results
        )

        sources = build_hts_sources(
            results
        )

        return {
            "question": question,
            "context": context,
            "sources": sources,
        }

    # --------------------------------------------------------
    # Document index
    # --------------------------------------------------------

    if not has_document_index():

        return {
            "question": question,
            "context": "",
            "sources": [],
        }

    index = load_index()
    chunks = load_chunks()

    if index is None or not chunks:

        return {
            "question": question,
            "context": "",
            "sources": [],
        }

    # --------------------------------------------------------
    # Intent
    # --------------------------------------------------------

    prepared = prepare_question(
        question
    )

    # --------------------------------------------------------
    # Hybrid retrieval
    # --------------------------------------------------------

    retrieval_results = retrieve_hybrid(
        prepared["query"],
        index,
        chunks,
        top_k=3
    )

    if not retrieval_results:

        return {
            "question": question,
            "context": "",
            "sources": [],
        }

    # --------------------------------------------------------
    # Document context
    # --------------------------------------------------------

    document_context = build_document_context(
        retrieval_results
    )

    # --------------------------------------------------------
    # History
    # --------------------------------------------------------

    history_context = build_history_context(
        conversation_messages
    )

    # --------------------------------------------------------
    # Final context
    # --------------------------------------------------------

    context = (
        document_context
        + history_context
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    if prepared["intent"] == "summary":

        question_for_llm = (
            "Summarize the document. "
            "Include the main topics and "
            "important points."
        )

    else:

        question_for_llm = question

    return {
        "question": question_for_llm,
        "context": context,
        "sources": build_sources(
            retrieval_results
        ),
    }