#封装通义千问 API 的调用。 提供两个函数：普通调用和流式调用。
import requests  #发送 HTTP 请求到通义千问 API
import json
import os


def call_llm(prompt: str, model: str = "qwen-max"):
    """普通调用"""
    api_key = os.getenv("DASHSCOPE_API_KEY")  #从 .env 文件读取 API Key
    if not api_key:
        return "请设置 DASHSCOPE_API_KEY 环境变量"
#API地址
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
#请求头
    headers = {
        "Authorization": f"Bearer {api_key}",  #身份认证
        "Content-Type": "application/json"   #发送的是 JSON 格式
    }
#请求体
    data = {
        "model": model,
        "input": {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "result_format": "message"  #返回格式为标准消息格式
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)  #发送post请求，30s超时
        result = response.json()
        return result["output"]["choices"][0]["message"]["content"]  #逐层读取内容
    except Exception as e:
        return f"调用失败: {str(e)}"


def call_llm_stream(prompt: str, model: str = "qwen-turbo"):
    """流式调用"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        yield "请设置 DASHSCOPE_API_KEY 环境变量"
        return

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "enable"  #允许流式
    }

    data = {
        "model": model,
        "input": {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "result_format": "message",
            "incremental_output": True  #只返回新增内容
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=60)
        for line in response.iter_lines():  #逐行读取响应内容（SSE 格式每行一条数据）
            if line:
                line_str = line.decode('utf-8')  #把字节转成字符串
                if line_str.startswith('data:'):  #只处理以 data: 开头的行（SSE 标准格式）
                    try:
                        json_str = line_str[5:].strip()  #去掉 data: 前缀，得到 JSON 字符串
                        if json_str and json_str != '[DONE]':  #忽略空行和结束标记
                            chunk = json.loads(json_str)
                            content = chunk.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content',
                                                                                                             '')
                            if content:
                                yield content
                    except:
                        pass
    except Exception as e:
        yield f"调用失败: {str(e)}"