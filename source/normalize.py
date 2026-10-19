"""Turns raw model output into a clean Level 1 record that matches the schema."""
import json
import re

PROVIDER_MAP = {"KESC": "KE", "KE": "KE", "LESCO": "LESCO", "IESCO": "IESCO"}

NUMERIC_FIELDS = [
    "sanctioned_load_kw", "previous_reading", "current_reading", "units_consumed",
    "total_charges", "total_taxes", "current_bill", "arrears",
    "payable_within_due_date", "payable_after_due_date",
]
SCHEMA_KEYS = [
    "provider", "tariff", "sanctioned_load_kw", "bill_month", "reading_date",
    "issue_date", "due_date", "previous_reading", "current_reading", "units_consumed",
    "charges", "total_charges", "taxes", "total_taxes", "current_bill", "arrears",
    "payable_within_due_date", "payable_after_due_date",
]


def parse_json_text(text: str) -> dict:
    """Pull the first JSON object out of the model's reply."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return json.loads(match.group(0))


def to_number(value):
    if value is None or isinstance(value, (int, float)):
        return value
    cleaned = str(value).replace("Rs.", "").replace(",", "").strip()
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def empty_record(bill_id: str) -> dict:
    """Schema with nulls, used when a bill cannot be read."""
    record = {key: None for key in SCHEMA_KEYS}
    record["charges"] = []
    record["taxes"] = []
    record["provider"] = PROVIDER_MAP.get(bill_id.split("_")[0].upper())
    return record


def normalize(data: dict, bill_id: str) -> dict:
    record = empty_record(bill_id)
    record.update({k: v for k, v in data.items() if k in SCHEMA_KEYS})

    # Provider comes from the file name prefix (KESC -> KE).
    record["provider"] = PROVIDER_MAP.get(bill_id.split("_")[0].upper(), record["provider"])

    for field in NUMERIC_FIELDS:
        record[field] = to_number(record[field])

    for group in ("charges", "taxes"):
        cleaned = []
        for item in record[group] or []:
            amount = to_number(item.get("amount"))
            if amount is not None:
                cleaned.append({"type": item.get("type", "other"), "amount": amount})
        record[group] = cleaned

    return record
