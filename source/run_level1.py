"""Level 1: extract bill details from bill images into output/level1.csv.

Usage (run from the source/ folder):
    python run_level1.py            # uses data/test/bills if it has images, else data/train/bills
    python run_level1.py --train    # always preview the training bills
    python run_level1.py --test     # always use the test bills
"""
import argparse
import csv
import json
import time
from pathlib import Path

from google import genai
from google.genai import types

import config
from normalize import empty_record, normalize, parse_json_text
from prompts import LEVEL1_PROMPT

TRAIN_DIR = Path("data/train/bills")
TEST_DIR = Path("data/test/bills")
OUTPUT_DIR = Path("../output")
CACHE_ROOT = Path("cache/level1")
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def find_images(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_TYPES)


def choose_source(choice: str) -> tuple[list[Path], str]:
    if choice == "train":
        return find_images(TRAIN_DIR), "train"
    if choice == "test":
        return find_images(TEST_DIR), "test"
    test_images = find_images(TEST_DIR)
    if test_images:
        return test_images, "test"
    return find_images(TRAIN_DIR), "train"


def extract_bill(client, image_path: Path, split: str) -> dict:
    cache_dir = CACHE_ROOT / split
    cache_file = cache_dir / f"{image_path.stem}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    image = types.Part.from_bytes(
        data=image_path.read_bytes(),
        mime_type=IMAGE_TYPES[image_path.suffix.lower()],
    )

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=config.MODEL_NAME,
                contents=[image, LEVEL1_PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
            record = normalize(parse_json_text(response.text), image_path.stem)
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            time.sleep(config.REQUEST_DELAY)
            return record
        except Exception as err:
            print(f"    attempt {attempt} failed: {err}")
            time.sleep(config.REQUEST_DELAY * attempt)

    print(f"    could not read {image_path.name}; writing nulls for it")
    return empty_record(image_path.stem)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--train", action="store_true", help="use training bills")
    group.add_argument("--test", action="store_true", help="use test bills")
    args = parser.parse_args()

    config.check_api_key()
    choice = "train" if args.train else "test" if args.test else "auto"
    images, split = choose_source(choice)
    if not images:
        raise SystemExit("No bill images found. Put .png/.jpg bills in source/data/train/bills or source/data/test/bills.")

    # Test runs write the official file. Training runs write a preview so they never overwrite it.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / ("level1.csv" if split == "test" else "level1_train_preview.csv")

    print(f"Using {len(images)} {split} bill(s). Model: {config.MODEL_NAME}")
    client = genai.Client(api_key=config.API_KEY)

    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bill_id", "json"])
        for image_path in images:
            print(f"  Extracting {image_path.name}")
            record = extract_bill(client, image_path, split)
            writer.writerow([image_path.stem, json.dumps(record, ensure_ascii=False)])

    print(f"Done. Wrote {len(images)} row(s) to {output_file.resolve()}")


if __name__ == "__main__":
    main()
