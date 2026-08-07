from backend.processing.pipeline import process_document
from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import create_index
from backend.retrieval.retriever import retrieve


def build_rag(file_path, question):
    """
    Complete RAG pipeline.
    """

    result = process_document(file_path)

    chunks = result["chunks"]

    embeddings = generate_embeddings(chunks)

    index = create_index(embeddings)

    context = retrieve(question, index, chunks)

    return context