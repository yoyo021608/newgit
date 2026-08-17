```text
个人知识库管理系统

基于 FastAPI + ChromaDB + 通义千问 的智能知识库问答系统。

功能

- 用户注册/登录（JWT 认证）
- 文档上传（支持 PDF、Word、TXT、Markdown）
- 智能问答（基于 RAG 检索 + 大模型回答）
- 答案溯源（显示答案来源）

技术栈

- FastAPI + SQLAlchemy + MySQL
- ChromaDB（向量数据库）
- 通义千问 API（LLM）
- JWT 认证

快速启动

1. 安装依赖

pip install -r requirements.txt

2. 配置环境变量

创建 .env 文件：

DATABASE_URL=mysql+pymysql://root:密码@localhost:3306/knowledge_base
OPENAI_API_KEY=你的OpenAI密钥（用于向量嵌入）
DASHSCOPE_API_KEY=你的通义千问密钥（用于LLM）

3. 初始化数据库

在 MySQL 中创建 knowledge_base 数据库，启动服务后会自动建表。

4. 启动服务

uvicorn main:app --reload

访问 http://127.0.0.1:8000/docs 查看 API 文档。

API 接口

/api/users/register POST 用户注册
/api/users/login POST 用户登录
/api/documents/upload POST 上传文档（需 token）
/api/documents/ GET 文档列表（需 token）
/api/documents/{id} DELETE 删除文档（需 token）
/api/qa/ask POST 智能问答（需 token）
```