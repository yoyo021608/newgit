import datetime

def get_current_weather(city: str) -> str:
    """获取指定城市的当前天气（模拟）"""
    weather_data = {
        "北京": "晴天，25°C",
        "上海": "多云，28°C",
        "广州": "小雨，30°C",
        "深圳": "晴，32°C",
        "成都": "阴天，22°C"
    }
    return weather_data.get(city, f"{city}：天气未知")


def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return "表达式包含不支持的字符"
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


def get_current_time() -> str:
    """获取当前时间"""
    now = datetime.datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


# 工具注册表
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "获取指定城市的当前天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海、成都"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式，支持加减乘除和括号",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如：1+2*3"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> str:
    """执行工具调用"""
    if tool_name == "get_current_weather":
        city = arguments.get("city", "北京")
        return get_current_weather(city)
    elif tool_name == "calculate":
        expression = arguments.get("expression", "")
        return calculate(expression)
    elif tool_name == "get_current_time":
        return get_current_time()
    else:
        return f"未知工具: {tool_name}"