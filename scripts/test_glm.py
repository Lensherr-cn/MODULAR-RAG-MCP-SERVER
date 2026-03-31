"""Test GLM LLM connection.

This script validates the GLM LLM configuration and API connectivity.
Based on test_qwen.py structure.
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
from src.libs.llm.glm_llm import GlmLLM, GlmLLMError
from src.libs.llm.base_llm import Message


def test_glm_connection():
    """Test GLM LLM connection with minimal setup."""
    print("=" * 50)
    print("Testing GLM LLM Connection")
    print("=" * 50)

    # Load settings
    try:
        settings = load_settings(project_root / "config" / "settings.yaml")
        print(f"✓ Settings loaded")

        # 尝试从 additional_llms 获取 GLM 配置
        glm_config = None
        if settings.additional_llms and "Glm" in settings.additional_llms:
            glm_config = settings.additional_llms["Glm"]
            print(f"  Found Glm in additional_llms")
        else:
            # 回退到主 llm 配置
            glm_config = settings.llm
            print(f"  Using main llm configuration")

        print(f"  Provider: {glm_config.provider}")
        print(f"  Model: {glm_config.model}")
        print(f"  Temperature: {glm_config.temperature}")
        print(f"  Max tokens: {glm_config.max_tokens}")
    except Exception as e:
        print(f"✗ ERROR loading settings: {e}")
        return False

    # Create GLM LLM instance with specific config
    try:
        llm = GlmLLM(settings=settings, llm_config=glm_config)
        print(f"✓ GlmLLM instance created")
        print(f"  Base URL: {llm.base_url}")
    except ValueError as e:
        print(f"✗ ERROR creating LLM: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

    # Test chat completion
    test_message = "你好，请用中文回复一句简短的问候。同时告诉我你是什么大语言模型"
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
    except GlmLLMError as e:
        print(f"\n✗ GLM API error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error during chat: {e}")
        return False

    print("\n" + "=" * 50)
    print("✓ GLM LLM Connection Test: SUCCESS")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = test_glm_connection()
    sys.exit(0 if success else 1)
