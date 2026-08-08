import json
import pickle
import re
from pathlib import Path

import faiss
import numpy as np

from backend.embeddings.embed_text import generate_embeddings


HTS_INDEX_DIR = Path("data/hts/index")

FAISS_PATH = HTS_INDEX_DIR / "hts.faiss"
BM25_PATH = HTS_INDEX_DIR / "bm25.pkl"
RECORDS_PATH = HTS_INDEX_DIR / "records.json"
TEXTS_PATH = HTS_INDEX_DIR / "texts.json"


class HTSRetriever:

    def __init__(self):
        self._load_indexes()

        self.hts_lookup = {}

        for idx, record in enumerate(self.records):
            htsno = str(
                record.get("htsno", "")
            ).strip()

            if htsno:
                self.hts_lookup[htsno] = idx

    # =================================================
    # LOAD
    # =================================================

    def _load_indexes(self):

        print("Loading HTS indexes...")

        self.faiss_index = faiss.read_index(
            str(FAISS_PATH)
        )

        with BM25_PATH.open("rb") as file:
            self.bm25 = pickle.load(file)

        with RECORDS_PATH.open(
            "r",
            encoding="utf-8"
        ) as file:
            self.records = json.load(file)

        with TEXTS_PATH.open(
            "r",
            encoding="utf-8"
        ) as file:
            self.texts = json.load(file)

        if not (
            self.faiss_index.ntotal
            == len(self.records)
            == len(self.texts)
        ):
            raise ValueError(
                "FAISS, records and texts are not aligned."
            )

        print(
            f"HTS indexes loaded: "
            f"{len(self.records)} records"
        )

    # =================================================
    # TOKENIZATION
    # =================================================

    def _tokenize(self, text):

        return re.findall(
            r"[a-zA-Z0-9]+",
            text.lower()
        )

    # =================================================
    # HTS CODE
    # =================================================

    def _extract_hts_code(self, query):

        matches = re.findall(
            r"\b\d{4}(?:\.\d{2}){0,3}\b",
            query
        )

        return matches[0] if matches else None

    def _exact_search(self, query):

        code = self._extract_hts_code(query)

        if not code:
            return None

        return self.hts_lookup.get(code)

    # =================================================
    # FAISS
    # =================================================

    def _dense_search(
        self,
        query,
        top_k
    ):

        embedding = generate_embeddings(
            [query]
        )[0]

        embedding = np.asarray(
            [embedding],
            dtype="float32"
        )

        k = min(
            top_k,
            self.faiss_index.ntotal
        )

        distances, indices = (
            self.faiss_index.search(
                embedding,
                k
            )
        )

        return [
            (int(idx), float(distance))
            for distance, idx
            in zip(
                distances[0],
                indices[0]
            )
            if idx != -1
        ]

    # =================================================
    # BM25
    # =================================================

    def _sparse_search(
        self,
        query,
        top_k
    ):

        tokens = self._tokenize(query)

        scores = self.bm25.get_scores(
            tokens
        )

        k = min(
            top_k,
            len(scores)
        )

        ranked = sorted(
            range(len(scores)),
            key=lambda idx: scores[idx],
            reverse=True
        )[:k]

        return [
            (idx, float(scores[idx]))
            for idx in ranked
        ]

    # =================================================
    # NORMALIZE
    # =================================================

    def _normalize_scores(self, results):

        if not results:
            return {}

        values = [
            score
            for _, score in results
        ]

        minimum = min(values)
        maximum = max(values)

        if maximum == minimum:

            return {
                idx: 1.0
                for idx, _ in results
            }

        return {
            idx: (
                (score - minimum)
                /
                (maximum - minimum)
            )
            for idx, score in results
        }

    # =================================================
    # HYBRID SCORE
    # =================================================

    def _hybrid_scores(
        self,
        dense_results,
        sparse_results
    ):

        dense_similarity = [
            (
                idx,
                1.0 / (1.0 + distance)
            )
            for idx, distance
            in dense_results
        ]

        dense = self._normalize_scores(
            dense_similarity
        )

        sparse = self._normalize_scores(
            sparse_results
        )

        indices = (
            set(dense)
            |
            set(sparse)
        )

        return {
            idx: (
                0.5 * dense.get(idx, 0.0)
                +
                0.5 * sparse.get(idx, 0.0)
            )
            for idx in indices
        }

    # =================================================
    # RRF
    # =================================================

    def _rrf_fusion(
        self,
        dense_results,
        sparse_results,
        top_k,
        rrf_k=60
    ):

        scores = {}

        for rank, (idx, _) in enumerate(
            dense_results
        ):

            scores[idx] = (
                scores.get(idx, 0.0)
                +
                1.0
                /
                (rrf_k + rank + 1)
            )

        for rank, (idx, _) in enumerate(
            sparse_results
        ):

            scores[idx] = (
                scores.get(idx, 0.0)
                +
                1.0
                /
                (rrf_k + rank + 1)
            )

        return sorted(
            scores,
            key=scores.get,
            reverse=True
        )[:top_k]

    # =================================================
    # QUERY TERMS
    # =================================================

    def _query_terms(self, query):

        stop_words = {
            "what",
            "is",
            "the",
            "a",
            "an",
            "for",
            "of",
            "to",
            "in",
            "on",
            "with",
            "which",
            "code",
            "hts",
            "tariff",
            "rate",
            "number",
            "tell",
            "me",
            "about",
            "give",
            "show",
            "does",
            "mean",
            "please",
        }

        tokens = self._tokenize(query)

        return [
            token
            for token in tokens
            if token not in stop_words
            and len(token) >= 3
        ]

    # =================================================
    # LEXICAL SCORE
    # =================================================

    def _lexical_score(
        self,
        query,
        text
    ):

        terms = self._query_terms(query)

        if not terms:
            return 0.0

        text_tokens = self._tokenize(
            text
        )

        text_set = set(
            text_tokens
        )

        weights = {
            "horse": 2.5,
            "horses": 2.5,
            "purebred": 2.0,
            "breeding": 1.2,
            "breed": 1.5,
            "live": 1.2,
            "animal": 1.2,
            "animals": 1.2,
        }

        total_weight = 0.0
        matched_weight = 0.0

        for term in terms:

            weight = weights.get(
                term,
                1.0
            )

            total_weight += weight

            if term in text_set:
                matched_weight += weight

        if total_weight == 0:
            return 0.0

        score = (
            matched_weight
            /
            total_weight
        )

        # Exact phrase bonus
        normalized_query = " ".join(terms)
        normalized_text = " ".join(text_tokens)

        if normalized_query in normalized_text:
            score += 0.20

        # All query concepts matched
        if all(
            term in text_set
            for term in terms
        ):
            score += 0.20

        return min(score, 1.0)

    # =================================================
    # HIERARCHY SCORE
    # =================================================

    def _hierarchy_score(self, idx):

        record = self.records[idx]

        htsno = str(
            record.get(
                "htsno",
                ""
            )
        ).strip()

        indent = str(
            record.get(
                "indent",
                ""
            )
        ).strip()

        score = 0.0

        # More specific HTS codes receive a small bonus.
        if htsno:

            parts = htsno.split(".")

            if len(parts) >= 3:
                score += 0.10

            if len(parts) >= 4:
                score += 0.05

        # Indented entries are generally more specific
        # than broad section headers.
        if indent:

            try:
                indent_value = int(indent)

                if indent_value > 0:
                    score += min(
                        indent_value * 0.01,
                        0.10
                    )

            except ValueError:
                pass

        return min(
            score,
            0.20
        )

    # =================================================
    # FORMAT
    # =================================================

    def _format_result(
        self,
        idx,
        relevance_score
    ):

        record = self.records[idx]

        return {
            "index": idx,

            "htsno": record.get(
                "htsno",
                ""
            ),

            "description": record.get(
                "description",
                ""
            ),

            "general": record.get(
                "general",
                ""
            ),

            "special": record.get(
                "special",
                ""
            ),

            "other": record.get(
                "other",
                ""
            ),

            "units": record.get(
                "units",
                []
            ),

            "footnotes": record.get(
                "footnotes",
                []
            ),

            "superior": record.get(
                "superior"
            ),

            "relevance_score": round(
                relevance_score,
                4
            ),

            "text": self.texts[idx],
        }

    # =================================================
    # SEARCH
    # =================================================

    def search(
        self,
        query,
        top_k=5,
        candidate_k=30,
        relevance_threshold=0.25
    ):

        if not query or not query.strip():
            return []

        # ---------------------------------------------
        # Exact code
        # ---------------------------------------------

        exact_index = self._exact_search(
            query
        )

        # ---------------------------------------------
        # Retrieve candidates
        # ---------------------------------------------

        dense_results = self._dense_search(
            query,
            candidate_k
        )

        sparse_results = self._sparse_search(
            query,
            candidate_k
        )

        hybrid_scores = self._hybrid_scores(
            dense_results,
            sparse_results
        )

        fused_indices = self._rrf_fusion(
            dense_results,
            sparse_results,
            candidate_k
        )

        # ---------------------------------------------
        # Final ranking
        # ---------------------------------------------

        final_scores = {}

        for idx in fused_indices:

            lexical = self._lexical_score(
                query,
                self.texts[idx]
            )

            hybrid = hybrid_scores.get(
                idx,
                0.0
            )

            hierarchy = self._hierarchy_score(
                idx
            )

            # Ranking weights:
            #
            # lexical   50%
            # hybrid    35%
            # hierarchy 15%

            score = (
                0.50 * lexical
                +
                0.35 * hybrid
                +
                0.15 * hierarchy
            )

            final_scores[idx] = score

        ranked = sorted(
            final_scores,
            key=final_scores.get,
            reverse=True
        )

        results = []

        # ---------------------------------------------
        # Exact code ALWAYS first
        # ---------------------------------------------

        if exact_index is not None:

            results.append(
                self._format_result(
                    exact_index,
                    1.0
                )
            )

            ranked = [
                idx
                for idx in ranked
                if idx != exact_index
            ]

        # ---------------------------------------------
        # Filter
        # ---------------------------------------------

        for idx in ranked:

            score = final_scores[idx]

            if score < relevance_threshold:
                continue

            results.append(
                self._format_result(
                    idx,
                    score
                )
            )

            if len(results) >= top_k:
                break

        # ---------------------------------------------
        # Fallback
        # ---------------------------------------------

        if (
            not results
            and ranked
        ):

            best = ranked[0]

            results.append(
                self._format_result(
                    best,
                    final_scores[best]
                )
            )

        return results


# =====================================================
# SINGLETON
# =====================================================

hts_retriever = None


def get_hts_retriever():
    global hts_retriever

    if hts_retriever is None:
        hts_retriever = HTSRetriever()

    return hts_retriever


def search_hts(
    query,
    top_k=5,
    relevance_threshold=0.25
):

    retriever = get_hts_retriever()

    return retriever.search(
        query,
        top_k=top_k,
        relevance_threshold=relevance_threshold
    )