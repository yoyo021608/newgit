# main.py 是 FastAPI 应用的入口文件，负责创建应用实例、注册中间件和路由。
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, documents, qa, sessions
from utils.mcp_server import mcp_app

# CORSMiddleware 跨域中间件，允许前端（不同端口）调用后端
app = FastAPI(title="个人知识库管理系统")

# 允许所有域名，携带token，所有HTTP请求，所有请求头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由，把路由模块挂载到应用上
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(qa.router)
app.include_router(sessions.router)

# 挂载 MCP 服务到 /mcp 路径，挂载到子路径上，和主应用互不影响
app.mount("/mcp", mcp_app)

@app.get("/")
def root():
    return {"message": "Hello World"}