from backend.ingestion.hts_parser import (
    parse_hts_file,
    hts_record_to_text,
)


file_path = "data/hts/hts_2026_revision_12.json"

records = parse_hts_file(file_path)

print("\n========== HTS PARSER TEST ==========\n")

print("Total normalized records:", len(records))

print("\n========== FIRST RECORD ==========\n")

print(hts_record_to_text(records[0]))

print("\n========== SAMPLE RECORDS ==========\n")

for i, record in enumerate(records[:5], 1):
    print(
        f"{i}. "
        f"{record['htsno']} - "
        f"{record['description']}"
    )