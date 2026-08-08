from rank_bm25 import BM25Okapi


def tokenize(text):
    return text.lower().split()


def create_bm25_index(chunks):
    tokenized_chunks = [tokenize(chunk) for chunk in chunks]

    return BM25Okapi(tokenized_chunks)


def search_bm25(bm25, query, top_k=5):
    query_tokens = tokenize(query)

    scores = bm25.get_scores(query_tokens)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    return ranked_indices, scores