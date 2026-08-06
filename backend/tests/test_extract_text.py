from ingestion.extract_text import extract_text

file_path = "../data/uploads/sample.pdf"

try:
    text = extract_text(file_path)

    print("=" * 60)
    print("TEXT EXTRACTION SUCCESSFUL")
    print("=" * 60)

    print(text[:1000])

except Exception as e:
    print("ERROR :", e)