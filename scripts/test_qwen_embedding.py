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
from src.libs.vector_store.chroma_store import ChromaStore


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


def test_store_to_chroma():
    """Test storing embeddings to ChromaDB."""
    print(f"\n\n{'=' * 60}")
    print("Bonus Test: Store Embeddings to ChromaDB")
    print(f"{'=' * 60}")

    try:
        settings = load_settings(project_root / "config" / "settings.yaml")
        embedding = QwenEmbedding(settings=settings)

        # 准备测试文档
        documents = [
            {"id": "doc_1", "text": "人工智能是计算机科学的一个分支。"},
            {"id": "doc_2", "text": "机器学习使用算法来从数据中学习。"},
            {"id": "doc_3", "text": "深度学习是机器学习的子领域。"},
        ]

        print(f"\n准备存储 {len(documents)} 个文档到 ChromaDB...")

        # 生成向量
        texts = [doc["text"] for doc in documents]
        embeddings_list = embedding.embed(texts)

        # 构建记录
        records = []
        for doc, emb in zip(documents, embeddings_list):
            record = {
                "id": doc["id"],
                "vector": emb,
                "metadata": {
                    "text": doc["text"],
                    "source": "test_script",
                }
            }
            records.append(record)
            print(f"  - {doc['id']}: 向量维度 {len(emb)}")

        # 初始化 ChromaDB
        print(f"\n初始化 ChromaDB...")
        chroma_store = ChromaStore(settings=settings)
        print(f"  ✓ ChromaDB 初始化成功")
        print(f"  - 集合名称：{chroma_store.collection_name}")
        print(f"  - 存储路径：{chroma_store.persist_directory}")

        # 存储向量
        print(f"\n存储向量到 ChromaDB...")
        chroma_store.upsert(records)
        print(f"  ✓ 成功存储 {len(records)} 条记录")

        # 验证存储
        stats = chroma_store.get_collection_stats()
        print(f"  - 集合中总记录数：{stats['count']}")

        # 简单查询测试
        print(f"\n查询测试...")
        query_text = "什么是人工智能？"
        query_embedding = embedding.embed([query_text])[0]

        results = chroma_store.query(vector=query_embedding, top_k=2)
        print(f"  查询：'{query_text}'")
        print(f"  找到 {len(results)} 个相关结果:")
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result['text']} (相似度：{result['score']:.4f})")

        print(f"\n✓ ChromaDB 存储测试成功!")
        return True

    except Exception as e:
        print(f"✗ ChromaDB 存储测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_qwen_embedding_connection()
    if success:
        print("\n是否继续测试 ChromaDB 存储？(y/n): ", end="")
        response = input().strip().lower()
        if response == 'y':
            chroma_success = test_store_to_chroma()
            success = success and chroma_success

    sys.exit(0 if success else 1)
