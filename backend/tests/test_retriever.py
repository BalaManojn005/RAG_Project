from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import (
    create_index,
)
from backend.retrieval.retriever import retrieve

chunks = [
    "Artificial Intelligence is changing the world.",
    "Machine Learning is a subset of Artificial Intelligence.",
    "Football is a popular sport.",
    "Deep Learning uses neural networks.",
    "Python is widely used in AI."
]

embeddings = generate_embeddings(chunks)

index = create_index(embeddings)

query = "Explain Artificial Intelligence"

results = retrieve(query, index, chunks)

print("\nTop Retrieved Chunks:\n")

for i, chunk in enumerate(results, start=1):
    print(f"{i}. {chunk}")