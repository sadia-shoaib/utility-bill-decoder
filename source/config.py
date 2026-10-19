"""Loads settings from source/.env (or the environment)."""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


def make_client():
    return genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=60000),  # milliseconds: 60 seconds
    )
load_dotenv()

MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "google")
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-3.1-flash-lite")
API_KEY = os.environ.get("API_KEY", "")

# Free tier allows 15 requests/min, so wait between calls.
REQUEST_DELAY = float(os.environ.get("REQUEST_DELAY", "4"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))


def check_api_key():
    if not API_KEY or API_KEY.startswith("your-"):
        raise SystemExit("API_KEY is not set. Add your Gemini key to source/.env first.")
