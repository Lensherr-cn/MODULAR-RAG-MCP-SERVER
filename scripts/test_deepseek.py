"""Test DeepSeek LLM connection.

This script validates the DeepSeek LLM configuration.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from src.core.settings import load_settings
from src.libs.llm.llm_factory import LLMFactory
from src.libs.llm.base_llm import Message


def test_deepseek_connection():
    """Test DeepSeek LLM connection."""
    print("=" * 50)
    print("Testing DeepSeek LLM Connection")
    print("=" * 50)

    # Check API key
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not found in environment variables")
        return False
    print(f"API Key found: {api_key[:10]}...{api_key[-4:]}")

    # Load settings
    try:
        settings = load_settings(project_root / "config" / "settings.yaml")
        print(f"Settings loaded successfully")
        print(f"  - LLM Provider: {settings.llm.provider}")
        print(f"  - LLM Model: {settings.llm.model}")
    except Exception as e:
        print(f"ERROR loading settings: {e}")
        return False

    # Create LLM instance
    try:
        llm = LLMFactory.create(settings)
        print(f"LLM instance created: {type(llm).__name__}")
    except Exception as e:
        print(f"ERROR creating LLM: {e}")
        return False

    # Test chat
    try:
        print("\nSending test message: 'Hello, please respond with a short greeting.'")
        response = llm.chat([
            Message(role="user", content="Hello, please respond with a short greeting.")
        ])
        print(f"\nResponse received:")
        print(f"  - Content: {response.content[:200]}...")
        print(f"  - Model: {response.model}")
        print(f"  - Usage: {response.usage}")
    except Exception as e:
        print(f"ERROR during chat: {e}")
        return False

    print("\n" + "=" * 50)
    print("DeepSeek LLM Connection Test: SUCCESS")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = test_deepseek_connection()
    sys.exit(0 if success else 1)
