from backend.processing.pipeline import process_document

file_path = "data/uploads/REPORT~1.PDF"

result = process_document(file_path)

print(result)