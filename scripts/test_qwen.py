"""Test Qwen LLM connection.

This script validates the Qwen LLM configuration and API connectivity.
Unlike test_deepseek.py, this focuses on essential validation without
duplicating logic already in qwen_llm.py.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(project_root / ".env")

from src.core.settings import load_settings
from src.libs.llm.qwen_llm import QwenLLM, QwenLLMError
from src.libs.llm.base_llm import Message


def test_qwen_connection():
    """Test Qwen LLM connection with minimal setup."""
    print("=" * 50)
    print("Testing Qwen LLM Connection")
    print("=" * 50)

    # Load settings
    try:
        settings = load_settings(project_root / "config" / "settings.yaml")
        print(f"✓ Settings loaded")
        print(f"  Model: {settings.llm.model}")
        print(f"  Temperature: {settings.llm.temperature}")
        print(f"  Max tokens: {settings.llm.max_tokens}")
    except Exception as e:
        print(f"✗ ERROR loading settings: {e}")
        return False

    # Create Qwen LLM instance directly
    try:
        llm = QwenLLM(settings=settings)
        print(f"✓ QwenLLM instance created")
        print(f"  Base URL: {llm.base_url}")
    except ValueError as e:
        print(f"✗ ERROR creating LLM: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

    # Test chat completion
    test_message = "你好，请用日语回复一句简短的问候。"
    print(f"\nSending test message: '{test_message}'")

    try:
        response = llm.chat([
            Message(role="user", content=test_message)
        ])
        print(f"\n✓ Response received:")
        print(f"  Content: {response.content[:150]}...")
        print(f"  Model: {response.model}")
        if response.usage:
            print(f"  Usage: {response.usage}")
    except QwenLLMError as e:
        print(f"\n✗ Qwen API error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error during chat: {e}")
        return False

    print("\n" + "=" * 50)
    print("✓ Qwen LLM Connection Test: SUCCESS")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = test_qwen_connection()
    sys.exit(0 if success else 1)
