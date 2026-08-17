import requests
import json
import os


def call_llm(prompt: str, model: str = "qwen-max"):
    """普通调用"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "请设置 DASHSCOPE_API_KEY 环境变量"

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "input": {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        return result["output"]["choices"][0]["message"]["content"]
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
        "X-DashScope-SSE": "enable"
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
            "incremental_output": True
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=60)
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data:'):
                    try:
                        json_str = line_str[5:].strip()
                        if json_str and json_str != '[DONE]':
                            chunk = json.loads(json_str)
                            content = chunk.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content',
                                                                                                             '')
                            if content:
                                yield content
                    except:
                        pass
    except Exception as e:
        yield f"调用失败: {str(e)}"