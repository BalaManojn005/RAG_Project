from backend.rag.rag_pipeline import is_hts_question
from backend.storage.storage import has_document_index


def test_hts_question_detection():
    assert is_hts_question("What is HTS 0101.21.00?")
    assert is_hts_question("What import tariff applies?")
    assert not is_hts_question("Summarize my document")


def test_document_index_state_is_a_boolean():
    assert isinstance(has_document_index(), bool)
