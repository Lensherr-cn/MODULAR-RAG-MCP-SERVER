"""
文件完整性检查功能 - PyCharm Debug 专用测试文件

使用说明:
1. 在 PyCharm 中打开此文件
2. 在左侧行号旁点击设置断点（建议断点位置已标注）
3. 右键 -> Debug 'test_file_integrity_debug'
4. 使用 F8 (Step Over) 或 F7 (Step Into) 逐步执行

建议断点位置:
- 第 45 行: 初始化 SQLiteIntegrityChecker
- 第 52 行: 计算文件哈希
- 第 58 行: 检查是否应该跳过
- 第 65 行: 标记成功
- 第 72 行: 再次检查跳过状态
"""

import os
import sys
import tempfile
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.libs.loader.file_integrity import SQLiteIntegrityChecker, FileIntegrityChecker


def debug_file_integrity():
    """
    文件完整性检查功能逐步调试

    调试步骤:
    1. 在此函数第一行设置断点
    2. Debug 运行此文件
    3. 使用 F8 逐步执行，观察变量变化
    """

    # ========== 步骤 1: 创建测试文件 ==========
    print("=" * 60)
    print("步骤 1: 创建测试文件")
    print("=" * 60)

    # 创建临时文件用于测试
    test_content = """
    这是一个测试文件，用于调试文件完整性检查功能。
    文件完整性检查使用 SHA256 哈希算法。
    如果文件内容不变，哈希值也不会改变。
    """

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.txt',
        delete=False,
        encoding='utf-8'
    )
    temp_file.write(test_content)
    temp_file_path = temp_file.name
    temp_file.close()

    print(f"✓ 创建临时文件: {temp_file_path}")
    print(f"✓ 文件内容长度: {len(test_content)} 字符")

    # 设置断点 1: 观察临时文件创建
    # <-- 在这里设置断点，检查 temp_file_path

    # ========== 步骤 2: 初始化完整性检查器 ==========
    print("\n" + "=" * 60)
    print("步骤 2: 初始化 SQLiteIntegrityChecker")
    print("=" * 60)

    # 使用测试数据库路径
    db_path = str(project_root / "data" / "db" / "debug_integrity.db")

    # 如果数据库已存在，先删除以进行干净测试
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ 删除旧的数据库: {db_path}")

    # 初始化检查器
    # 这里会创建 SQLite 数据库和表结构
    integrity_checker = SQLiteIntegrityChecker(db_path=db_path)

    print(f"✓ 初始化 SQLiteIntegrityChecker")
    print(f"✓ 数据库路径: {db_path}")
    print(f"✓ 数据库文件存在: {os.path.exists(db_path)}")

    # 设置断点 2: 观察检查器初始化
    # <-- 在这里设置断点，检查 integrity_checker 对象

    # ========== 步骤 3: 计算文件哈希 ==========
    print("\n" + "=" * 60)
    print("步骤 3: 计算文件 SHA256 哈希")
    print("=" * 60)

    # 计算文件的 SHA256 哈希
    # 这是文件完整性检查的核心，相同的文件内容总是产生相同的哈希值
    file_hash = integrity_checker.compute_sha256(temp_file_path)

    print(f"✓ 文件哈希: {file_hash}")
    print(f"✓ 哈希长度: {len(file_hash)} 字符 (SHA256 固定为 64 位十六进制)")

    # 验证哈希一致性：再次计算应该得到相同结果
    file_hash_2 = integrity_checker.compute_sha256(temp_file_path)
    print(f"✓ 再次计算哈希: {file_hash_2}")
    print(f"✓ 哈希一致: {file_hash == file_hash_2}")

    # 设置断点 3: 观察哈希计算
    # <-- 在这里设置断点，检查 file_hash 值

    # ========== 步骤 4: 检查是否应该跳过 ==========
    print("\n" + "=" * 60)
    print("步骤 4: 检查是否应该跳过处理")
    print("=" * 60)

    # 第一次检查：文件从未处理过，应该返回 False
    should_skip_first = integrity_checker.should_skip(file_hash)

    print(f"✓ 第一次检查 should_skip: {should_skip_first}")
    print(f"  说明: 文件从未处理过，应该继续处理")

    # 设置断点 4: 观察第一次跳过检查
    # <-- 在这里设置断点，检查 should_skip_first

    # ========== 步骤 5: 模拟文件处理并标记成功 ==========
    print("\n" + "=" * 60)
    print("步骤 5: 模拟文件处理完成，标记成功")
    print("=" * 60)

    # 模拟文件处理流程...
    print("  模拟处理中...")
    print("  - 解析 PDF")
    print("  - 分块")
    print("  - 生成向量")
    print("  - 存储到数据库")

    # 标记文件处理成功
    # 这会向 ingestion_history 表插入一条记录
    integrity_checker.mark_success(
        file_hash=file_hash,
        file_path=temp_file_path,
        collection="debug_test"
    )

    print(f"✓ 标记成功: file_hash={file_hash[:16]}...")
    print(f"✓ 集合: debug_test")

    # 设置断点 5: 观察标记成功
    # <-- 在这里设置断点，检查数据库是否写入

    # ========== 步骤 6: 再次检查跳过状态 ==========
    print("\n" + "=" * 60)
    print("步骤 6: 再次检查是否应该跳过")
    print("=" * 60)

    # 第二次检查：文件已处理成功，应该返回 True
    should_skip_second = integrity_checker.should_skip(file_hash)

    print(f"✓ 第二次检查 should_skip: {should_skip_second}")
    print(f"  说明: 文件已处理成功，应该跳过（零成本增量更新）")

    # 设置断点 6: 观察第二次跳过检查
    # <-- 在这里设置断点，检查 should_skip_second

    # ========== 步骤 7: 列出已处理文件 ==========
    print("\n" + "=" * 60)
    print("步骤 7: 列出已处理文件记录")
    print("=" * 60)

    # 列出所有已处理的文件
    all_records = integrity_checker.list_processed()

    print(f"✓ 总记录数: {len(all_records)}")
    for record in all_records:
        print(f"\n  记录详情:")
        print(f"    - file_hash: {record['file_hash'][:16]}...")
        print(f"    - file_path: {record['file_path']}")
        print(f"    - collection: {record.get('collection', 'N/A')}")
        print(f"    - processed_at: {record['processed_at']}")

    # 按集合筛选
    debug_records = integrity_checker.list_processed(collection="debug_test")
    print(f"\n✓ debug_test 集合记录数: {len(debug_records)}")

    # 设置断点 7: 观察查询结果
    # <-- 在这里设置断点，检查 all_records

    # ========== 步骤 8: 测试失败标记 ==========
    print("\n" + "=" * 60)
    print("步骤 8: 测试失败标记功能")
    print("=" * 60)

    # 创建另一个测试文件
    temp_file_2 = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file_2.write("另一个测试文件内容")
    temp_file_2_path = temp_file_2.name
    temp_file_2.close()

    file_hash_2 = integrity_checker.compute_sha256(temp_file_2_path)

    # 标记失败
    integrity_checker.mark_failed(
        file_hash=file_hash_2,
        file_path=temp_file_2_path,
        error_msg="模拟处理失败: PDF 解析错误"
    )

    print(f"✓ 标记失败: file_hash={file_hash_2[:16]}...")

    # 失败的文件不应该被跳过（允许重试）
    should_skip_failed = integrity_checker.should_skip(file_hash_2)
    print(f"✓ 失败文件 should_skip: {should_skip_failed}")
    print(f"  说明: 失败的文件不会跳过，允许重试")

    # 设置断点 8: 观察失败标记
    # <-- 在这里设置断点

    # ========== 步骤 9: 测试删除记录 ==========
    print("\n" + "=" * 60)
    print("步骤 9: 测试删除记录功能")
    print("=" * 60)

    # 删除成功记录
    removed = integrity_checker.remove_record(file_hash)
    print(f"✓ 删除记录: {removed}")

    # 删除后应该不再跳过
    should_skip_after_remove = integrity_checker.should_skip(file_hash)
    print(f"✓ 删除后 should_skip: {should_skip_after_remove}")
    print(f"  说明: 记录删除后，文件可以重新处理")

    # 设置断点 9: 观察删除操作
    # <-- 在这里设置断点

    # ========== 清理 ==========
    print("\n" + "=" * 60)
    print("清理")
    print("=" * 60)

    # 关闭数据库连接
    integrity_checker.close()
    print("✓ 关闭数据库连接")

    # 删除临时文件
    os.unlink(temp_file_path)
    os.unlink(temp_file_2_path)
    print(f"✓ 删除临时文件")

    # 可选：删除测试数据库
    # os.remove(db_path)
    # print(f"✓ 删除测试数据库: {db_path}")

    print("\n" + "=" * 60)
    print("调试完成！")
    print("=" * 60)


def debug_hash_computation_detail():
    """
    详细调试哈希计算过程

    如果你想深入了解 SHA256 哈希是如何计算的，使用此函数
    """
    print("\n" + "=" * 60)
    print("详细调试: SHA256 哈希计算")
    print("=" * 60)

    import hashlib

    # 创建测试文件
    test_content = b"Hello, World! " * 1000  # 重复内容以模拟大文件

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(test_content)
        temp_path = f.name

    try:
        # 方法 1: 一次性读取（小文件）
        print("\n方法 1: 一次性读取")
        with open(temp_path, 'rb') as f:
            content = f.read()
            hash1 = hashlib.sha256(content).hexdigest()
        print(f"  哈希: {hash1}")

        # 方法 2: 分块读取（大文件推荐，内存友好）
        print("\n方法 2: 分块读取 (64KB 每块)")
        sha256 = hashlib.sha256()
        with open(temp_path, 'rb') as f:
            chunk_num = 0
            while True:
                chunk = f.read(65536)  # 64KB
                if not chunk:
                    break
                chunk_num += 1
                sha256.update(chunk)
                print(f"  块 {chunk_num}: {len(chunk)} 字节")
        hash2 = sha256.hexdigest()
        print(f"  最终哈希: {hash2}")

        # 验证两种方法结果一致
        print(f"\n✓ 两种方法结果一致: {hash1 == hash2}")

    finally:
        os.unlink(temp_path)


def debug_database_schema():
    """
    查看数据库表结构

    如果你想查看 SQLite 数据库的内部结构，使用此函数
    """
    print("\n" + "=" * 60)
    print("调试: 数据库表结构")
    print("=" * 60)

    import sqlite3

    db_path = str(project_root / "data" / "db" / "debug_integrity.db")

    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查看表结构
    print("\n表列表:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")

    # 查看 ingestion_history 表结构
    print("\ningestion_history 表结构:")
    cursor.execute("PRAGMA table_info(ingestion_history)")
    for row in cursor.fetchall():
        print(f"  - {row[1]} ({row[2]})")

    # 查看索引
    print("\n索引列表:")
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")

    # 查看数据
    print("\n表数据:")
    cursor.execute("SELECT * FROM ingestion_history")
    rows = cursor.fetchall()
    print(f"  总记录数: {len(rows)}")
    for row in rows:
        print(f"  {row}")

    conn.close()


if __name__ == "__main__":
    # 主调试函数
    debug_file_integrity()

    # 可选：运行其他调试函数
    # debug_hash_computation_detail()
    # debug_database_schema()


def test_file_integrity():
    """Pytest 格式的测试函数"""
    debug_file_integrity()


def test_hash_computation():
    """Pytest 格式的哈希计算测试"""
    debug_hash_computation_detail()


def test_database_schema():
    """Pytest 格式的数据库结构测试"""
    debug_database_schema()
