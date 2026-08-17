from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, documents, qa
from utils.mcp_server import mcp_app

app = FastAPI(title="个人知识库管理系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(qa.router)

# 挂载 MCP 服务到 /mcp 路径
app.mount("/mcp", mcp_app)

@app.get("/")
def root():
    return {"message": "Hello World"}