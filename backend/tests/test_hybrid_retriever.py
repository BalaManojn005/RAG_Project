from backend.retrieval.hybrid_retriever import retrieve_hybrid
from backend.embeddings.embed_text import generate_embeddings
from backend.vectorstore.faiss_store import create_index


chunks = [
    "The company maintains calibration certificates and service reports.",
    "Employee involvement is an important element of quality standards.",
    "The company plans to expand educational partnerships and skill development.",
]

embeddings = generate_embeddings(chunks)

index = create_index(embeddings)

query = "quality standards employee involvement"

results = retrieve_hybrid(
    query,
    index,
    chunks,
    top_k=3
)

print("\n========== HYBRID RESULTS ==========\n")

for i, result in enumerate(results, 1):
    print(f"{i}. {result}")