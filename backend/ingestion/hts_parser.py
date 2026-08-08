import json
from pathlib import Path


def load_hts_data(file_path):
    """Load the raw HTS JSON dataset."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"HTS file not found: {file_path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("HTS JSON must contain a list of records.")

    return data


def normalize_hts_record(record):
    """Convert one raw HTS record into a clean record."""

    return {
        "htsno": str(record.get("htsno", "")).strip(),
        "indent": str(record.get("indent", "")).strip(),
        "description": str(record.get("description", "")).strip(),
        "superior": record.get("superior"),
        "units": record.get("units", []),
        "general": str(record.get("general", "")).strip(),
        "special": str(record.get("special", "")).strip(),
        "other": str(record.get("other", "")).strip(),
        "footnotes": record.get("footnotes", []),
        "quotaQuantity": str(
            record.get("quotaQuantity", "")
        ).strip(),
        "additionalDuties": str(
            record.get("additionalDuties", "")
        ).strip(),
    }


def parse_hts_file(file_path):
    """Load and normalize the complete HTS dataset."""

    raw_records = load_hts_data(file_path)

    records = []

    for record in raw_records:
        normalized = normalize_hts_record(record)

        if normalized["htsno"] or normalized["description"]:
            records.append(normalized)

    return records


def hts_record_to_text(record):
    """Convert an HTS record into searchable text."""

    parts = []

    if record["htsno"]:
        parts.append(f"HTS Number: {record['htsno']}")

    if record["description"]:
        parts.append(f"Description: {record['description']}")

    if record["superior"]:
        parts.append(f"Parent HTS: {record['superior']}")

    if record["units"]:
        parts.append(
            f"Units: {', '.join(map(str, record['units']))}"
        )

    if record["general"]:
        parts.append(f"General Rate: {record['general']}")

    if record["special"]:
        parts.append(f"Special Rate: {record['special']}")

    if record["other"]:
        parts.append(f"Other Rate: {record['other']}")

    if record["footnotes"]:
        parts.append(f"Footnotes: {record['footnotes']}")

    if record["quotaQuantity"]:
        parts.append(
            f"Quota Quantity: {record['quotaQuantity']}"
        )

    if record["additionalDuties"]:
        parts.append(
            f"Additional Duties: {record['additionalDuties']}"
        )

    return "\n".join(parts)