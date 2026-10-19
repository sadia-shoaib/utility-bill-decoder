"""Checks that your API key and model work. Run this first."""
from pathlib import Path

from google import genai
from google.genai import types

import config

config.check_api_key()
client = config.make_client()

reply = client.models.generate_content(
    model=config.MODEL_NAME,
    contents="Reply with the single word: ready",
)
print("Text test:", reply.text.strip())

bill = Path("data/train/bills/KESC_0008.png")
if bill.exists():
    image = types.Part.from_bytes(data=bill.read_bytes(), mime_type="image/png")
    reply = client.models.generate_content(
        model=config.MODEL_NAME,
        contents=[image, "What is the Current Month units value on this bill? Number only."],
    )
    print("Image test:", reply.text.strip(), "(expected 151)")
else:
    print("Image test skipped: KESC_0008.png not found in data/train/bills")
