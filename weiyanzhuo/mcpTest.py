from my_llm import llm, search_knowledge

# ========== 方式 1: 使用封装的便捷函数 ==========

print("=" * 60)
print("🔍 搜索知识库：RAG 是什么？")
print("=" * 60)

result_text = search_knowledge("RAG 是什么？", top_k=3)
print(result_text)

print("\n✅ 查询完成\n")

# ========== 方式 2: 直接使用 MCP Client ==========
#
# from my_llm import mcp_client
#
# print("=" * 60)
# print("📋 查看可用的 MCP 工具")
# print("=" * 60)
#
# try:
#     mcp_client.start()
#
#     # 列出所有可用工具
#     tools = mcp_client.list_tools()
#     print(f"\n发现 {len(tools)} 个可用工具:\n")
#
#     for tool in tools:
#         print(f"  • {tool['name']}")
#         print(f"    {tool['description'][:100]}...")
#         print()
#
#     # 调用特定工具
#     print("=" * 60)
#     print("🔧 调用 query_knowledge_hub 工具")
#     print("=" * 60)
#
#     result = mcp_client.call_tool(
#         tool_name="query_knowledge_hub",
#         arguments={
#             "query": "混合检索的工作原理",
#             "top_k": 5
#         }
#     )
#
#     # 格式化输出
#     content_blocks = result.get("content", [])
#     for i, block in enumerate(content_blocks, 1):
#         if block.get("type") == "text":
#             print(f"\n[结果 {i}]")
#             print(block.get("text", "")[:500])  # 只显示前 500 字
#
#     if result.get("isError"):
#         print("\n⚠️  工具执行失败")
#
# finally:
#     mcp_client.stop()
#
# print("\n✅ 全部完成")