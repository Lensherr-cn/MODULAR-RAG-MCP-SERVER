import os

from dotenv import load_dotenv

load_dotenv(override=True)

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL")