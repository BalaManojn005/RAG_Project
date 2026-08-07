from backend.rag.rag_pipeline import build_rag

file_path = "data/uploads/report.pdf"

question = "What is this document about?"

context = build_rag(file_path, question)

print("\nRetrieved Context:\n")

for i, chunk in enumerate(context, 1):
    print(f"{i}. {chunk}")