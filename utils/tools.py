import datetime
import requests

#天气
def get_current_weather(city: str) -> str:
    try:
        # 1. 先查缓存
        from utils.cache import cache_get, cache_set
        cache_key = f"weather:{city}"
        cached = cache_get(cache_key)
        if cached:
            print(f"✅ 天气缓存命中: {city}")
            return cached

        # 2. 缓存未命中，调用 API
        url = f"https://wttr.in/{city}?format=%C+%t"  #调用免费天气 API，%C 返回天气状况，%t 返回温度
        response = requests.get(url, timeout=5)
        if response.status_code == 200:  #请求成功
            weather = response.text.strip()
            if weather:
                # 英文天气转中文
                weather_map = {
                    "Light rain shower": "阵雨",
                    "Thundery outbreak possible": "雷阵雨",
                    "Partly cloudy": "多云",
                    "Patchy rain nearby": "小雨",
                    "Light rain": "小雨",
                    "Moderate rain": "中雨",
                    "Heavy rain": "大雨",
                    "Sunny": "晴",
                    "Clear": "晴",
                    "Cloudy": "阴",
                    "Overcast": "阴",
                    "Mist": "雾",
                    "Fog": "雾"
                }
                for en, zh in weather_map.items():
                    if en in weather:
                        weather = weather.replace(en, zh)  #替换为中文
                        #break
                weather = weather.replace("+", "")
                result = f"{city}：{weather}"

                # 3. 存入缓存，有效期 10 分钟
                cache_set(cache_key, result, expire=600)
                print(f"✅ 天气已缓存: {city}")

                return result
            else:
                return f"{city}：天气查询失败"
        else:
            return f"{city}：天气查询失败"
    except Exception as e:
        return f"{city}：天气查询失败"


#计算
def calculate(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/().% ")  #允许的字符集合（安全过滤）
        if not all(c in allowed for c in expression):
            return "表达式包含不支持的字符"
        result = eval(expression)  #执行数学表达式
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


#时间
def get_current_time() -> str:
    import datetime
    import pytz
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now(tz)
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


# 工具注册表，给 LLM 看的工具说明书
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "获取指定城市的当前天气信息",
            "parameters": {  #参数定义
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

#执行工具调用
def execute_tool(tool_name: str, arguments: dict) -> str:
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