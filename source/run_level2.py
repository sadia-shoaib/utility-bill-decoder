"""Level 2: answer the 12 customer questions for every test bill.

Run after run_level1.py --test (it needs output/level1.csv):
    python run_level2.py

Writes output/level2.csv with the same rows and order as data/test/csv/level2.csv.
"""
import csv
import json
from pathlib import Path

from google import genai

import config
from facts import build_facts
from level2_history import extract_history
from llm import call_json
from normalize import empty_record
from prompts import ANSWER_PROMPT

QUESTIONS_CSV = Path("data/test/csv/level2.csv")
LEVEL1_CSV = Path("../output/level1.csv")
OUTPUT_CSV = Path("../output/level2.csv")
ANSWER_CACHE = Path("cache/level2/answers")


def load_level1() -> dict:
    if not LEVEL1_CSV.exists():
        raise SystemExit("output/level1.csv not found. Run: python run_level1.py --test")
    with LEVEL1_CSV.open(encoding="utf-8-sig", newline="") as f:
        return {row["bill_id"]: json.loads(row["json"]) for row in csv.DictReader(f) if row["json"].strip()}


def read_template() -> list[dict]:
    if not QUESTIONS_CSV.exists():
        raise SystemExit("data/test/csv/level2.csv not found. Copy the test templates into source/data/test/csv/.")
    with QUESTIONS_CSV.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_prompt(record: dict, facts: dict, questions: dict) -> str:
    question_lines = "\n".join(f"{qid}: {text}" for qid, text in questions.items())
    return (
        ANSWER_PROMPT
        + "\n\nBILL DATA:\n" + json.dumps(record, ensure_ascii=False)
        + "\n\nFACTS:\n" + json.dumps(facts, ensure_ascii=False)
        + "\n\nQUESTIONS:\n" + question_lines
    )


def answer_bill(client, bill_id: str, record: dict, facts: dict, questions: dict) -> dict:
    cache_file = ANSWER_CACHE / f"{bill_id}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    answers, pending = {}, dict(questions)
    for _ in range(2):  # second pass only re-asks questions the model skipped
        if not pending:
            break
        data = call_json(client, [build_prompt(record, facts, pending)])
        for qid in pending:
            value = data.get(qid)
            if value:
                answers[qid] = str(value).strip()
        pending = {q: t for q, t in pending.items() if q not in answers}
    for qid in pending:
        answers[qid] = "Not available: the model did not return an answer. Re-run run_level2.py."

    ANSWER_CACHE.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
    return answers


def main():
    config.check_api_key()
    level1 = load_level1()
    rows = read_template()
    bill_ids = list(dict.fromkeys(r["bill_id"] for r in rows))

    print(f"Answering {len(rows)} questions for {len(bill_ids)} bill(s). Model: {config.MODEL_NAME}")
    client = genai.Client(api_key=config.API_KEY)

    answers_by_bill = {}
    for bill_id in bill_ids:
        print(f"  {bill_id}")
        record = level1.get(bill_id)
        if record is None:
            print("    no Level 1 record found; answers will say the data is missing")
            record = empty_record(bill_id)
        history = extract_history(client, bill_id)
        facts = build_facts(record, history)
        questions = {r["question_id"]: r["question"] for r in rows if r["bill_id"] == bill_id}
        answers_by_bill[bill_id] = answer_bill(client, bill_id, record, facts, questions)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    blanks = 0
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bill_id", "question_id", "question", "answer"])
        for r in rows:
            answer = answers_by_bill.get(r["bill_id"], {}).get(r["question_id"], "")
            blanks += 0 if answer else 1
            writer.writerow([r["bill_id"], r["question_id"], r["question"], answer])

    print(f"Done. Wrote {len(rows)} row(s) to {OUTPUT_CSV.resolve()}")
    if blanks:
        print(f"Warning: {blanks} answer(s) are empty. Re-run the script.")


if __name__ == "__main__":
    main()
