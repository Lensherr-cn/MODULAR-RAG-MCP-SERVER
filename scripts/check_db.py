#!/usr/bin/env python
"""Database Check Script - 检查 ChromaDB 和 BM25 索引状态

用法:
    python scripts/check_db.py
    
功能:
    1. 检查 ChromaDB 中的数据量
    2. 检查 BM25 索引文件是否存在
    3. 验证 collection 名称配置
    4. 测试基本的查询功能
"""

import sys
from pathlib import Path

# Ensure project root is on path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.settings import load_settings
from src.libs.vector_store.vector_store_factory import VectorStoreFactory
from src.ingestion.storage.bm25_indexer import BM25Indexer


def print_section(title: str):
    """打印分隔线标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_chromadb(settings):
    """检查 ChromaDB 状态"""
    print_section("📊 ChromaDB 状态检查")
    
    try:
        print(f"\n配置信息:")
        print(f"  • Provider: {settings.vector_store.provider}")
        print(f"  • Collection: {settings.vector_store.collection_name}")
        print(f"  • Persist Directory: {settings.vector_store.persist_directory}")
        
        # 创建 vector store
        vector_store = VectorStoreFactory.create(settings)
        
        # 获取统计信息
        stats = vector_store.get_collection_stats()
        
        print(f"\n集合统计:")
        print(f"  • 名称: {stats['name']}")
        print(f"  • 总记录数: {stats['count']}")
        print(f"  • 元数据: {stats['metadata']}")
        
        if stats['count'] == 0:
            print("\n⚠️  警告: ChromaDB 集合是空的！")
            print("   请先运行文档摄入流程:")
            print("   python scripts/ingest.py --path <文档路径> --collection knowledge-hub")
            return False
        else:
            print(f"\n✅ ChromaDB 包含 {stats['count']} 条向量记录")
            return True
            
    except Exception as e:
        print(f"\n❌ ChromaDB 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_bm25_index(settings):
    """检查 BM25 索引状态"""
    print_section("🔍 BM25 索引状态检查")
    
    try:
        # 尝试不同的 collection 名称变体
        possible_names = [
            settings.vector_store.collection_name,  # knowledge-hub (优先)
            settings.vector_store.collection_name.replace('-', '_'),  # knowledge_hub (备选)
        ]
        
        # 使用项目根目录（scripts 的父目录）作为基准
        project_root = Path(__file__).parent.parent
        bm25_base_dir = project_root / "data" / "db" / "bm25"
        print(f"\nBM25 基础目录: {bm25_base_dir}")
        print(f"当前工作目录: {Path.cwd()}")
        print(f"项目根目录: {project_root}")
        print(f"尝试的 Collection 名称: {possible_names}")
        
        index_found = False
        for collection_name in possible_names:
            index_dir = bm25_base_dir / collection_name
            index_file = index_dir / f"{collection_name}_bm25.json"
            
            print(f"\n  检查: {collection_name}")
            print(f"    • 索引目录: {index_dir}")
            print(f"    • 索引文件: {index_file}")
            print(f"    • 绝对路径: {Path(index_file).absolute()}")
            
            if Path(index_file).exists():
                file_size = Path(index_file).stat().st_size / 1024  # KB
                print(f"    ✅ 索引文件存在 ({file_size:.1f} KB)")
                
                # 尝试加载索引
                try:
                    indexer = BM25Indexer(index_dir=str(index_dir))
                    loaded = indexer.load(collection=collection_name)
                    if loaded:
                        print(f"    ✅ 索引加载成功")
                        
                        # 显示索引元数据
                        metadata = indexer._metadata
                        if metadata:
                            print(f"    • 文档数量: {metadata.get('num_docs', 'N/A')}")
                            print(f"    • 平均文档长度: {metadata.get('avg_doc_length', 'N/A'):.1f}")
                            print(f"    • 词项总数: {metadata.get('total_terms', 'N/A')}")
                        
                        index_found = True
                        break
                    else:
                        print(f"    ⚠️  索引加载失败")
                except Exception as e:
                    print(f"    ❌ 索引加载错误: {e}")
            else:
                print(f"    ❌ 索引文件不存在")
        
        if not index_found:
            print("\n⚠️  警告: 未找到可用的 BM25 索引！")
            print("   BM25 索引会在文档摄入时自动创建")
            return False
        else:
            print("\n✅ BM25 索引可用")
            return True
            
    except Exception as e:
        print(f"\n❌ BM25 索引检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query(settings):
    """测试查询功能"""
    print_section("🧪 查询功能测试")
    
    try:
        from src.core.query_engine.dense_retriever import create_dense_retriever
        from src.core.query_engine.sparse_retriever import create_sparse_retriever
        from src.libs.embedding.embedding_factory import EmbeddingFactory
        
        print("\n初始化检索组件...")
        
        # 创建 embedding
        embedding_client = EmbeddingFactory.create(settings)
        print("  ✅ Embedding 客户端就绪")
        
        # 创建 vector store
        vector_store = VectorStoreFactory.create(settings)
        print("  ✅ Vector Store 就绪")
        
        # 创建 dense retriever
        dense_retriever = create_dense_retriever(
            settings=settings,
            embedding_client=embedding_client,
            vector_store=vector_store,
        )
        print("  ✅ Dense Retriever 就绪")
        
        # 创建 sparse retriever（使用与配置一致的 collection 名称）
        bm25_collection = settings.vector_store.collection_name
        project_root = Path(__file__).parent.parent
        bm25_index_path = project_root / "data" / "db" / "bm25" / bm25_collection
        bm25_indexer = BM25Indexer(index_dir=str(bm25_index_path))
        sparse_retriever = create_sparse_retriever(
            settings=settings,
            bm25_indexer=bm25_indexer,
            vector_store=vector_store,
        )
        sparse_retriever.default_collection = bm25_collection
        print(f"  ✅ Sparse Retriever 就绪 (collection: {bm25_collection})")
        
        # 测试 Dense Retrieval
        print("\n测试 Dense Retrieval...")
        test_query = "能源装备"
        dense_results = dense_retriever.retrieve(
            query=test_query,
            top_k=3,
        )
        print(f"  • 查询: '{test_query}'")
        print(f"  • 返回结果数: {len(dense_results)}")
        if dense_results:
            print(f"  • 最佳匹配分数: {dense_results[0].score:.4f}")
        
        # 测试 Sparse Retrieval
        print("\n测试 Sparse Retrieval...")
        try:
            sparse_results = sparse_retriever.retrieve(
                keywords=["能源"],
                top_k=3,
            )
            print(f"  • 关键词: ['能源']")
            print(f"  • 返回结果数: {len(sparse_results)}")
            if sparse_results:
                print(f"  • 最佳匹配分数: {sparse_results[0].score:.4f}")
        except Exception as e:
            print(f"  ⚠️  Sparse Retrieval 测试失败: {e}")
        
        print("\n✅ 查询功能测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 查询功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "🔍" * 35)
    print("  RAG 数据库检查工具")
    print("🔍" * 35)
    
    # 加载配置
    try:
        settings = load_settings("config/settings.yaml")
        print("✅ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return 1
    
    # 执行检查
    chromadb_ok = check_chromadb(settings)
    bm25_ok = check_bm25_index(settings)
    query_ok = test_query(settings) if (chromadb_ok or bm25_ok) else False
    
    # 总结
    print_section("📋 检查总结")
    print(f"\n  ChromaDB:        {'✅ 正常' if chromadb_ok else '❌ 异常'}")
    print(f"  BM25 Index:      {'✅ 正常' if bm25_ok else '❌ 异常'}")
    print(f"  查询功能:        {'✅ 正常' if query_ok else '❌ 异常'}")
    
    if chromadb_ok and bm25_ok:
        print("\n🎉 所有组件都正常工作！")
    elif not chromadb_ok and not bm25_ok:
        print("\n⚠️  系统需要初始化：")
        print("   1. 准备 PDF 文档")
        print("   2. 运行摄入脚本:")
        print("      python scripts/ingest.py --path <文档路径> --collection knowledge-hub")
    else:
        print("\n⚠️  部分组件异常，请检查上述错误信息")
    
    print("\n" + "=" * 70 + "\n")
    
    return 0 if (chromadb_ok or bm25_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
