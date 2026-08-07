from backend.embeddings.embed_text import generate_embeddings

chunks = [
    "Artificial Intelligence is transforming the world.",
    "Machine Learning is a subset of Artificial Intelligence.",
    "I like playing football."
]

embeddings = generate_embeddings(chunks)

print("Number of embeddings:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))