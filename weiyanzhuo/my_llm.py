from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from env_utils import QWEN_API_KEY, QWEN_BASE_URL

# 调用gemini
llm = ChatOpenAI(
    model_name="qwen3.5-plus",
    temperature=1.3,
    api_key=QWEN_API_KEY,
    base_url=QWEN_BASE_URL
)

import json
import subprocess
import sys
from typing import Any, Dict, List, Optional


class SimpleMCPClient:
    """简单的 MCP 客户端，用于快速测试"""

    def __init__(self, server_module: str = "src.mcp_server.server"):
        self.server_module = server_module
        self._process: Optional[subprocess.Popen] = None

    def start(self):
        """启动 MCP Server"""
        self._process = subprocess.Popen(
            [sys.executable, "-m", self.server_module],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "clientInfo": {"name": "simple-client", "version": "1.0.0"},
                "capabilities": {}
            }
        }
        self._process.stdin.write(json.dumps(init_request) + "\n")
        self._process.stdin.flush()
        self._process.stdout.readline()

        # Initialized 通知
        init_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        self._process.stdin.write(json.dumps(init_notification) + "\n")
        self._process.stdin.flush()

        print("✅ MCP Server 已启动并初始化")

    def stop(self):
        """停止 MCP Server"""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except:
                self._process.kill()
            print("🛑 MCP Server 已停止")

    def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用的工具列表"""
        assert self._process is not None, "请先调用 start()"

        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        self._process.stdin.write(json.dumps(request) + "\n")
        self._process.stdin.flush()

        response = json.loads(self._process.stdout.readline().strip())

        if "error" in response:
            raise RuntimeError(f"Failed to list tools: {response['error']}")

        return response.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定的工具"""
        assert self._process is not None, "请先调用 start()"

        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        self._process.stdin.write(json.dumps(request) + "\n")
        self._process.stdin.flush()

        response = json.loads(self._process.stdout.readline().strip())

        if "error" in response:
            raise RuntimeError(f"Tool call failed: {response['error']}")

        return response.get("result", {})

    def query_knowledge(self, query: str, top_k: int = 5, collection: Optional[str] = None) -> str:
        """便捷方法：查询知识库"""
        args = {"query": query, "top_k": top_k}
        if collection:
            args["collection"] = collection

        result = self.call_tool("query_knowledge_hub", args)

        # 提取文本内容
        texts = []
        for block in result.get("content", []):
            if block.get("type") == "text":
                texts.append(block.get("text", ""))

        return "\n".join(texts)


# 创建全局 MCP 客户端实例
mcp_client = SimpleMCPClient()


# 便捷的查询函数
def search_knowledge(query: str, top_k: int = 3):
    """快速搜索知识库"""
    try:
        mcp_client.start()
        result = mcp_client.query_knowledge(query, top_k)
        return result
    finally:
        mcp_client.stop()

