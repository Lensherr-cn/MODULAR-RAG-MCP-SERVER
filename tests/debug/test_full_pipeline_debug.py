"""
完整数据摄取流水线 - PyCharm Debug 专用测试文件

使用说明:
1. 在 PyCharm 中打开此文件
2. 在左侧行号旁点击设置断点
3. 右键 -> Debug 'test_full_pipeline_debug'
4. 使用 F8 (Step Over) 或 F7 (Step Into) 逐步执行

建议断点位置:
- 第 55 行: 查找 PDF 文件
- 第 75 行: 初始化 Pipeline
- 第 85 行: 运行 Pipeline
- 第 95 行: 检查结果
"""

import os
import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.settings import load_settings
from src.ingestion.pipeline import IngestionPipeline


def find_pdf_file():
    """自动查找可用的 PDF 测试文件"""

    # 可能的 PDF 文件路径（按优先级）
    possible_paths = [
        # 1. 用户指定的 test.pdf
        project_root / "data" / "documents" / "test.pdf",
        # 2. 任何在 data/documents/ 下的 PDF
        *list((project_root / "data" / "documents").glob("*.pdf")),
        # 3. 项目自带的测试 PDF
        project_root / "tests" / "fixtures" / "sample_documents" / "simple.pdf",
        project_root / "tests" / "fixtures" / "sample_documents" / "blogger_intro.pdf",
    ]

    for path in possible_paths:
        if path.exists():
            print(f"✓ 找到 PDF 文件: {path}")
            return str(path)

    # 如果没找到，列出目录内容帮助诊断
    print("✗ 未找到 PDF 文件，检查以下目录:")
    for check_dir in [
        project_root / "data" / "documents",
        project_root / "tests" / "fixtures" / "sample_documents"
    ]:
        print(f"\n  目录: {check_dir}")
        if check_dir.exists():
            files = list(check_dir.glob("*.pdf"))
            if files:
                for f in files:
                    print(f"    - {f.name}")
            else:
                print("    (空目录)")
        else:
            print("    (目录不存在)")

    return None


def debug_full_pipeline():
    """
    完整摄取流水线逐步调试

    这会一步一步执行完整的 6 阶段流水线：
    1. File Integrity Check
    2. Document Loading (PDF -> Markdown)
    3. Chunking
    4. Transform (Refine + Enrich + Caption)
    5. Encoding (Dense + Sparse)
    6. Storage (Chroma + BM25 + Image)
    """

    # ========== 步骤 1: 查找 PDF 文件 ==========
    print("=" * 60)
    print("步骤 1: 查找 PDF 测试文件")
    print("=" * 60)

    pdf_path = find_pdf_file()
    if not pdf_path:
        print("\n✗ 错误: 没有找到 PDF 文件!")
        print("\n请确保以下之一:")
        print("  1. 将 test.pdf 放到 data/documents/ 目录")
        print("  2. 或修改 find_pdf_file() 函数指定其他路径")
        return

    # 设置断点 1: 确认 PDF 路径
    # <-- 在这里设置断点，检查 pdf_path

    # ========== 步骤 2: 加载配置 ==========
    print("\n" + "=" * 60)
    print("步骤 2: 加载配置")
    print("=" * 60)

    config_path = project_root / "config" / "settings.yaml"
    print(f"配置文件: {config_path}")
    print(f"配置文件存在: {config_path.exists()}")

    if not config_path.exists():
        print("✗ 错误: 配置文件不存在!")
        return

    settings = load_settings(str(config_path))
    print(f"✓ 配置加载成功")
    print(f"  LLM Provider: {settings.llm.provider}")
    print(f"  Embedding Provider: {settings.embedding.provider}")
    print(f"  Chunk Size: {settings.ingestion.chunk_size}")

    # 设置断点 2: 检查配置
    # <-- 在这里设置断点，检查 settings 对象

    # ========== 步骤 3: 初始化 Pipeline ==========
    print("\n" + "=" * 60)
    print("步骤 3: 初始化 IngestionPipeline")
    print("=" * 60)

    collection_name = "debug_test"
    force_reprocess = True  # 设为 True 强制重新处理

    print(f"集合名称: {collection_name}")
    print(f"强制重新处理: {force_reprocess}")

    # 这会初始化所有 6 个阶段的组件
    pipeline = IngestionPipeline(
        settings=settings,
        collection=collection_name,
        force=force_reprocess
    )

    print("✓ Pipeline 初始化完成")
    print(f"  组件列表:")
    print(f"    - integrity_checker: {type(pipeline.integrity_checker).__name__}")
    print(f"    - loader: {type(pipeline.loader).__name__}")
    print(f"    - chunker: {type(pipeline.chunker).__name__}")
    print(f"    - chunk_refiner: {type(pipeline.chunk_refiner).__name__}")
    print(f"    - metadata_enricher: {type(pipeline.metadata_enricher).__name__}")
    print(f"    - image_captioner: {type(pipeline.image_captioner).__name__}")
    print(f"    - dense_encoder: {type(pipeline.dense_encoder).__name__}")
    print(f"    - sparse_encoder: {type(pipeline.sparse_encoder).__name__}")
    print(f"    - batch_processor: {type(pipeline.batch_processor).__name__}")
    print(f"    - vector_upserter: {type(pipeline.vector_upserter).__name__}")
    print(f"    - bm25_indexer: {type(pipeline.bm25_indexer).__name__}")
    print(f"    - image_storage: {type(pipeline.image_storage).__name__}")

    # 设置断点 3: 检查 Pipeline 组件
    # <-- 在这里设置断点，检查 pipeline 对象

    # ========== 步骤 4: 运行 Pipeline ==========
    print("\n" + "=" * 60)
    print("步骤 4: 运行 Pipeline (6 阶段)")
    print("=" * 60)

    try:
        # 这是核心执行函数，会依次执行 6 个阶段
        result = pipeline.run(pdf_path)

        # 设置断点 4: 检查执行结果
        # <-- 在这里设置断点，检查 result 对象

    except Exception as e:
        print(f"✗ Pipeline 执行出错: {e}")
        import traceback
        traceback.print_exc()
        pipeline.close()
        return

    # ========== 步骤 5: 检查结果 ==========
    print("\n" + "=" * 60)
    print("步骤 5: 检查结果")
    print("=" * 60)

    print(f"✓ 执行成功: {result.success}")
    print(f"  文件路径: {result.file_path}")
    print(f"  文档 ID: {result.doc_id}")
    print(f"  Chunk 数量: {result.chunk_count}")
    print(f"  图片数量: {result.image_count}")
    print(f"  向量数量: {len(result.vector_ids)}")

    if not result.success:
        print(f"\n✗ 错误信息: {result.error}")

    # 设置断点 5: 检查结果详情
    # <-- 在这里设置断点

    # ========== 步骤 6: 查看各阶段详情 ==========
    print("\n" + "=" * 60)
    print("步骤 6: 各阶段执行详情")
    print("=" * 60)

    for stage_name, stage_data in result.stages.items():
        print(f"\n【{stage_name}】")
        if isinstance(stage_data, dict):
            for key, value in stage_data.items():
                # 截断长文本
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"  {key}: {value}")
        else:
            print(f"  {stage_data}")

    # 设置断点 6: 查看各阶段数据
    # <-- 在这里设置断点

    # ========== 步骤 7: 验证存储结果 ==========
    print("\n" + "=" * 60)
    print("步骤 7: 验证存储结果")
    print("=" * 60)

    # 检查 ChromaDB
    chroma_dir = project_root / "data" / "db" / "chroma"
    print(f"ChromaDB 目录: {chroma_dir}")
    print(f"  存在: {chroma_dir.exists()}")

    # 检查 BM25 索引
    bm25_dir = project_root / "data" / "db" / "bm25" / collection_name
    print(f"BM25 索引目录: {bm25_dir}")
    print(f"  存在: {bm25_dir.exists()}")

    # 检查图片存储
    image_dir = project_root / "data" / "images" / collection_name
    print(f"图片存储目录: {image_dir}")
    print(f"  存在: {image_dir.exists()}")
    if image_dir.exists():
        images = list(image_dir.glob("**/*.png")) + list(image_dir.glob("**/*.jpg"))
        print(f"  图片数量: {len(images)}")

    # ========== 清理 ==========
    print("\n" + "=" * 60)
    print("步骤 8: 清理资源")
    print("=" * 60)

    pipeline.close()
    print("✓ Pipeline 资源已释放")

    print("\n" + "=" * 60)
    print("调试完成！")
    print("=" * 60)


def test_file_only():
    """仅测试文件完整性检查（不需要 API 密钥）"""
    from src.libs.loader.file_integrity import SQLiteIntegrityChecker

    print("=" * 60)
    print("仅测试文件完整性检查")
    print("=" * 60)

    # 查找 PDF
    pdf_path = find_pdf_file()
    if not pdf_path:
        return

    # 初始化检查器
    db_path = project_root / "data" / "db" / "debug_integrity.db"
    checker = SQLiteIntegrityChecker(str(db_path))

    # 计算哈希
    file_hash = checker.compute_sha256(pdf_path)
    print(f"\n文件: {pdf_path}")
    print(f"哈希: {file_hash}")

    # 检查是否应该跳过
    should_skip = checker.should_skip(file_hash)
    print(f"应该跳过: {should_skip}")

    # 标记成功
    checker.mark_success(file_hash, pdf_path, "debug_test")
    print("✓ 已标记为成功")

    # 再次检查
    should_skip = checker.should_skip(file_hash)
    print(f"再次检查应该跳过: {should_skip}")

    checker.close()
    print("✓ 测试完成")


if __name__ == "__main__":
    # 主调试函数 - 完整流水线
    debug_full_pipeline()

    # 可选：仅测试文件完整性（取消注释下行）
    # test_file_only()


def test_full_pipeline():
    """Pytest 格式的测试函数"""
    debug_full_pipeline()


def test_file_integrity_only():
    """Pytest 格式的文件完整性测试"""
    test_file_only()
