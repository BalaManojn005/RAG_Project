from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import (
    create_index,
    save_index,
    load_index,
    search,
)

chunks = [
    "Artificial Intelligence is changing the world.",
    "Machine Learning is a subset of AI.",
    "Football is a popular sport."
]

embeddings = generate_embeddings(chunks)

index = create_index(embeddings)

save_index(index, "data/faiss_index/index.faiss")

index = load_index("data/faiss_index/index.faiss")

query = generate_embeddings(
    ["What is Artificial Intelligence?"]
)[0]

distances, indices = search(index, query)

print("Distances:", distances)
print("Indices:", indices)