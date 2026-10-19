"""Single place where Gemini is called. Returns parsed JSON."""
import time

from google.genai import types

import config
from normalize import parse_json_text


def call_json(client, contents):
    last_error = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=config.MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
            data = parse_json_text(response.text)
            time.sleep(config.REQUEST_DELAY)
            return data
        except Exception as err:
            last_error = err
            print(f"    attempt {attempt} failed: {err}")
            time.sleep(config.REQUEST_DELAY * attempt)
    raise RuntimeError(f"Model call failed after {config.MAX_RETRIES} attempts: {last_error}")
