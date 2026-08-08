from backend.rag.rag_pipeline import (
    ingest_document,
    ask_question,
)

file_path = "data/uploads/report.pdf"

print(ingest_document(file_path))

print()

question = "What are the company's quality standards?"

answer = ask_question(question)

print("========== AI ANSWER ==========\n")

print(answer)