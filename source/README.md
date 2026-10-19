# Utility Bill Decoder

An AI assistant for Pakistani electricity bills (K-Electric/KESC, LESCO and IESCO). For each bill image it:

- **Level 1 (extraction):** returns one JSON object with the bill's tariff, readings, dates, charges, taxes and payable amounts, without personal identifiers.
- **Level 2 (explanation):** answers 12 customer questions per bill in plain English, using only the bill's contents, with figures calculated in code.

## Runtime

- Python 3.13 (Python 3.11 or later should also work)
- Operating system: Windows 11 (commands below use PowerShell; macOS/Linux equivalents are given where they differ)
- Pinned dependencies: `source/requirements.txt`

## Project structure

```text
output/
  level1.csv                    generated: bill_id, json
  level2.csv                    generated: bill_id, question_id, question, answer
source/
  .env.example                  environment variable template (no real key)
  requirements.txt              pinned Python packages
  README.md                     this file
  config.py                     loads settings from .env
  prompts.py                    Level 1 and Level 2 prompts
  normalize.py                  parses and cleans model output to the schema
  llm.py                        single place that calls Gemini (retries, JSON output)
  run_level1.py                 Level 1 pipeline: bill images -> output/level1.csv
  level2_history.py             extracts usage chart and billing history for Level 2
  facts.py                      calculations for Level 2 (done in Python, not by the model)
  run_level2.py                 Level 2 pipeline: questions -> output/level2.csv
  test_gemini.py                checks the API key and model
  data/
    test/bills/                 test bill images
    test/csv/                   level1.csv and level2.csv templates
    train/bills/               training bill images
```

## Setup

Run all commands from the `source/` folder.

1. Create and activate a virtual environment.

   Windows (PowerShell):
```powershell
   python -m venv .venv
   .venv\Scripts\activate
```

   macOS / Linux:
```bash
   python3 -m venv .venv
   source .venv/bin/activate
```

2. Install the pinned dependencies.
```bash
   pip install -r requirements.txt
```

3. Create the environment file. Copy `.env.example` to `.env` and set your key:
```env
   MODEL_PROVIDER=google
   MODEL_NAME=gemini-3.1-flash-lite
   API_KEY=your-api-key-here
```
   `.env` is never included in the submission.

4. Place the bill images:
   - Test bills: `source/data/test/bills/` (10 images)
   - Training bills (optional, for preview only): `source/data/train/bills/`

## Run

The full pipeline is three commands, run in this order:

```bash
python test_gemini.py           # 1. checks the key and model; expect "ready" and 151
python run_level1.py --test     # 2. writes ../output/level1.csv (10 rows)
python run_level2.py            # 3. writes ../output/level2.csv (120 answers)
```

Optional: preview Level 1 on the training bills. This writes `../output/level1_train_preview.csv` and does not overwrite the official file:

```bash
python run_level1.py --train
```

Results are cached in `source/cache/`, so repeating a run does not repeat paid model calls. Delete that folder to force fresh results.

Run step 3 only after step 2, because Level 2 reads `output/level1.csv`.

## Approach

**Level 1 (extraction).** Each bill image is sent to Gemini with a prompt that defines the JSON schema and the extraction rules: values as printed, credits and subsidies negative, dates in `YYYY-MM-DD` or `YYYY-MM`, `null` for unavailable values, no personal identifiers. The model is asked for JSON output at temperature 0. `normalize.py` then extracts the JSON from the reply, derives the provider from the file name (`KESC` becomes `KE`), converts numeric strings to numbers, and fills every schema field, using `null` where the bill gives no value. If a bill cannot be read after the retries, its row is written with all fields `null` rather than invented values.

**Level 2 (explanations).** Two steps per bill:

1. The model extracts the 12-month usage chart, the billing and payment history, and any net-metering signs from the image. These are not part of the Level 1 schema.
2. `facts.py` calculates every figure the questions need in plain Python: highest-usage month, averages, same month last year, summer vs winter, recent trend, late payment increase, tax share and the estimates. The model never does the arithmetic. It receives the bill data, these calculated facts and the questions, and writes short English answers. It is instructed to use only that information, to label estimates and to say when the bill does not show a value.

Answers are cached, and a second pass re-asks any question the model skipped.

## Known limitations

- Level 2 history depends on how clearly the usage chart and payment table can be read. Where they cannot be read, the answer says the bill does not show the value.
- The FPA question refers to the current month, because the bill shows one month's FPA line.
- "Expected next month" and "monthly set-aside" figures are estimates based on the bill's own history, and are labelled as such.

## AI usage

- **Models:** Google Gemini `gemini-3.1-flash-lite` for Level 1 extraction, Level 2 history extraction and Level 2 answer writing.
- **APIs and services:** Google AI Studio Gemini API, accessed with the `google-genai` Python SDK.
- **Invoice or receipt extraction services:** none.
- **Local OCR libraries:** none.
- **AI coding tools:** Claude (Anthropic) was used to help draft the project code and this README. All code was reviewed and run by the author.

## Dependencies

Exact versions are in `requirements.txt`.

- `google-genai==TODO`: Gemini API client
- `python-dotenv==TODO`: loads `.env`