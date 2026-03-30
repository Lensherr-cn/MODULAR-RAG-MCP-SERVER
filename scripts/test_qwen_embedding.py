"""Test Qwen Embedding connection.

This script validates the Qwen Embedding configuration and API connectivity.
It tests the embedding generation for single and batch texts.
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
from src.libs.embedding.qwen_embedding import QwenEmbedding, QwenEmbeddingError


def test_qwen_embedding_connection():
    """Test Qwen Embedding connection with minimal setup."""
    print("=" * 50)
    print("Testing Qwen Embedding Connection")
    print("=" * 50)

    # Load settings
    try:
        settings = load_settings(project_root / "config" / "settings.yaml")
        print(f"✓ Settings loaded")

        # Try to get Qwen embedding config from additional_llms
        qwen_config = None
        if hasattr(settings, 'additional_llms') and settings.additional_llms and "qwen" in settings.additional_llms:
            qwen_config = settings.additional_llms["qwen"]
            print(f"  Found Qwen in additional_llms")
        else:
            # Fallback to main embedding config
            qwen_config = settings.embedding
            print(f"  Using main embedding configuration")

        print(f"  Provider: {qwen_config.provider}")
        print(f"  Model: {qwen_config.model}")
        print(f"  Dimensions: {getattr(qwen_config, 'dimensions', 'Not specified')}")
    except Exception as e:
        print(f"✗ ERROR loading settings: {e}")
        return False

    # Create Qwen Embedding instance
    try:
        embedding = QwenEmbedding(settings=settings)
        print(f"✓ QwenEmbedding instance created")
        print(f"  Base URL: {embedding.base_url}")
        print(f"  Model: {embedding.model}")
    except ValueError as e:
        print(f"✗ ERROR creating embedding: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

    # Test 1: Single text embedding
    print(f"\n{'=' * 50}")
    print("Test 1: Single Text Embedding")
    print(f"{'=' * 50}")

    test_text = "你好，这是一个测试文本。"
    print(f"Input text: '{test_text}'")

    try:
        embeddings = embedding.embed([test_text])
        print(f"✓ Embedding generated successfully")
        print(f"  Vector length: {len(embeddings[0])}")
        print(f"  First 5 values: {embeddings[0][:5]}")
        print(f"  Last 5 values: {embeddings[0][-5:]}")

        # Verify dimension
        expected_dim = embedding.get_dimension()
        actual_dim = len(embeddings[0])
        if expected_dim and expected_dim != actual_dim:
            print(f"  ⚠ Warning: Expected dimension {expected_dim}, got {actual_dim}")
        else:
            print(f"  ✓ Dimension matches expected: {actual_dim}")
    except QwenEmbeddingError as e:
        print(f"✗ Qwen Embedding API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during embedding: {e}")
        return False

    # Test 2: Batch embedding
    print(f"\n{'=' * 50}")
    print("Test 2: Batch Text Embedding")
    print(f"{'=' * 50}")

    batch_texts = [
        "今天天气很好。",
        "机器学习非常有趣。",
        "自然语言处理是 AI 的重要分支。",
        "向量数据库可以存储高维向量。"
    ]
    print(f"Input texts ({len(batch_texts)} items):")
    for i, text in enumerate(batch_texts, 1):
        print(f"  {i}. {text}")

    try:
        batch_embeddings = embedding.embed(batch_texts)
        print(f"\n✓ Batch embeddings generated successfully")
        print(f"  Number of vectors: {len(batch_embeddings)}")
        print(f"  Vector length: {len(batch_embeddings[0])}")

        # Verify all vectors have same dimension
        dimensions = [len(vec) for vec in batch_embeddings]
        if len(set(dimensions)) == 1:
            print(f"  ✓ All vectors have consistent dimension: {dimensions[0]}")
        else:
            print(f"  ✗ Inconsistent dimensions: {dimensions}")
            return False

        # Verify output count matches input count
        if len(batch_embeddings) == len(batch_texts):
            print(f"  ✓ Output count matches input count")
        else:
            print(f"  ✗ Output count mismatch: expected {len(batch_texts)}, got {len(batch_embeddings)}")
            return False

    except QwenEmbeddingError as e:
        print(f"✗ Qwen Embedding API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during batch embedding: {e}")
        return False

    # Test 3: Empty input validation
    print(f"\n{'=' * 50}")
    print("Test 3: Input Validation (Empty List)")
    print(f"{'=' * 50}")

    try:
        embedding.embed([])
        print(f"  ✗ Should have raised ValueError for empty input")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error type: {type(e).__name__}: {e}")
        return False

    # Test 4: Invalid input validation (non-string)
    print(f"\n{'=' * 50}")
    print("Test 4: Input Validation (Non-string)")
    print(f"{'=' * 50}")

    try:
        embedding.embed(["valid text", 123, "another valid"])  # type: ignore
        print(f"  ✗ Should have raised ValueError for non-string input")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error type: {type(e).__name__}: {e}")
        return False

    print(f"\n{'=' * 50}")
    print("✓ Qwen Embedding Connection Test: SUCCESS")
    print(f"{'=' * 50}")
    print("\nSummary:")
    print(f"  ✓ Single text embedding: PASSED")
    print(f"  ✓ Batch embedding: PASSED")
    print(f"  ✓ Input validation: PASSED")
    print(f"  ✓ Model: {embedding.model}")
    print(f"  ✓ Dimension: {embedding.get_dimension()}")
    return True


if __name__ == "__main__":
    success = test_qwen_embedding_connection()
    sys.exit(0 if success else 1)
