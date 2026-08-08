from backend.intent.handler import prepare_question
from backend.processing.pipeline import process_document
from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import create_index
from backend.retrieval.retriever import retrieve
from backend.llm.llm_client import generate_answer
from backend.storage.storage import (
    save_index,
    load_index,
    save_chunks,
    load_chunks,
)


def ingest_document(file_path):
    """
    Process a document only once.
    """

    result = process_document(file_path)

    chunks = result["chunks"]

    embeddings = generate_embeddings(chunks)

    index = create_index(embeddings)

    save_index(index)
    save_chunks(chunks)

    return "Document indexed successfully."


def ask_question(question):
    index = load_index()
    chunks = load_chunks()

    prepared = prepare_question(question)

    context = retrieve(
        prepared["query"],
        index,
        chunks
    )

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

    return generate_answer(
        question,
        "\n\n".join(context)
    )