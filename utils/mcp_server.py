from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils.tools import get_current_weather, calculate, get_current_time
import uvicorn
import threading
import os

mcp_app = FastAPI(title="MCP Server", version="1.0.0")


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict


class ToolCallResponse(BaseModel):
    result: str
    status: str


@mcp_app.get("/tools")
def list_tools():
    return {
        "tools": [
            {"name": "get_current_weather", "description": "获取城市天气"},
            {"name": "calculate", "description": "计算数学表达式"},
            {"name": "get_current_time", "description": "获取当前时间"}
        ]
    }


@mcp_app.post("/call", response_model=ToolCallResponse)
def call_tool(request: ToolCallRequest):
    tool_map = {
        "get_current_weather": get_current_weather,
        "calculate": calculate,
        "get_current_time": get_current_time
    }

    func = tool_map.get(request.tool)
    if not func:
        raise HTTPException(status_code=404, detail=f"工具 {request.tool} 不存在")

    try:
        if request.tool == "get_current_weather":
            city = request.arguments.get("city", "北京")
            result = func(city)
        elif request.tool == "calculate":
            expression = request.arguments.get("expression", "")
            result = func(expression)
        elif request.tool == "get_current_time":
            result = func()
        else:
            result = "未知工具"

        return ToolCallResponse(result=result, status="success")
    except Exception as e:
        return ToolCallResponse(result=str(e), status="error")