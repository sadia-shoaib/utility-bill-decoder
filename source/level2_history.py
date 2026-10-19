"""Extracts the usage chart and billing history that Level 1 does not cover."""
import json
from pathlib import Path

from google.genai import types

from llm import call_json
from prompts import HISTORY_PROMPT

BILLS_DIR = Path("data/test/bills")
CACHE_DIR = Path("cache/level2/history")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def find_bill_image(bill_id: str) -> Path:
    for ext in MIME:
        path = BILLS_DIR / f"{bill_id}{ext}"
        if path.exists():
            return path
    raise FileNotFoundError(f"No image for {bill_id} in {BILLS_DIR}")


def extract_history(client, bill_id: str) -> dict:
    cache_file = CACHE_DIR / f"{bill_id}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    path = find_bill_image(bill_id)
    image = types.Part.from_bytes(data=path.read_bytes(), mime_type=MIME[path.suffix.lower()])
    data = call_json(client, [image, HISTORY_PROMPT])

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
