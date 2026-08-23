#mcp客户端，通过 HTTP 请求调用 MCP 服务端的工具
import requests
import json

def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """通过 MCP 调用工具"""
    try:
        response = requests.post(
            "http://localhost:8001/mcp/call",
            json={"tool": tool_name, "arguments": arguments},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("result", "调用成功但无返回结果")
        else:
            return f"MCP 调用失败: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "MCP 服务未启动"
    except Exception as e:
        return f"MCP 调用异常: {str(e)}"