import json
from utils.llm_client import call_llm
from utils.tools import TOOLS
from utils.mcp_client import call_mcp_tool


def should_use_tools(user_question: str) -> bool:
    keywords = ["天气", "计算", "几点了", "现在", "多少", "加", "减", "乘", "除", "温度", "℃", "°C"]
    return any(k in user_question for k in keywords)


def tool_agent(question: str) -> str:
    if not should_use_tools(question):
        return None

    tools_desc = "\n".join([
        f"- {t['function']['name']}: {t['function']['description']}"
        for t in TOOLS
    ])

    prompt = f"""你是一个工具调用助手。根据用户的问题，决定调用哪个工具，并给出工具名和参数。

可用工具：
{tools_desc}

用户问题：{question}

请以 JSON 格式返回，格式如下：
{{"tool": "工具名", "arguments": {{"参数名": "参数值"}}}}

如果不需要调用工具，返回 {{"tool": "none"}}"""

    try:
        response = call_llm(prompt)
        result = json.loads(response)
        tool_name = result.get("tool")
        arguments = result.get("arguments", {})

        if tool_name and tool_name != "none":
            # 通过 MCP 调用工具
            return call_mcp_tool(tool_name, arguments)
        return None
    except:
        return None