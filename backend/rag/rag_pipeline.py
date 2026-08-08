from backend.intent.handler import prepare_question
from backend.processing.pipeline import process_document
from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import create_index
from backend.retrieval.hybrid_retriever import retrieve_hybrid
from backend.llm.llm_client import generate_answer
from backend.storage.storage import (
    save_index,
    load_index,
    save_chunks,
    load_chunks,
)


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


def ask_question(question):
    """
    Answer a question using hybrid sparse + dense retrieval.
    """

    # Load stored document index and chunks
    index = load_index()
    chunks = load_chunks()

    # Detect intent and prepare the retrieval query
    prepared = prepare_question(question)

    # Hybrid retrieval:
    # FAISS = dense semantic search
    # BM25  = sparse keyword search
    # RRF   = combines both rankings
    context = retrieve_hybrid(
        prepared["query"],
        index,
        chunks,
        top_k=3
    )

    # Handle document summary requests
    if prepared["intent"] == "summary":
        summary_prompt = (
            "Summarize the following document content. "
            "Include the main topics and important points. "
            "Do not invent information.\n\n"
            + "\n\n".join(context)
        )

        return generate_answer(
            "Summarize the document.",
            summary_prompt
        )

    # Normal question
    return generate_answer(
        question,
        "\n\n".join(context)
    )