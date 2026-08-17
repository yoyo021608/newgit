个人知识库管理系统

基于 FastAPI + ChromaDB + 通义千问 的智能知识库问答系统。


功能

- 用户注册/登录/忘记密码（JWT 认证）
- 文档上传/列表/删除（支持 PDF、Word、TXT、Markdown）
- 智能问答（RAG 检索 + 大模型流式回答）
- 快速问答（工具调用：计算/天气/时间/翻译/总结/代码解释）
- 答案溯源（显示答案来源文档）
- 历史记录保存与加载


技术栈

- FastAPI + SQLAlchemy + MySQL
- ChromaDB（向量数据库）
- 通义千问 API（LLM）
- JWT 认证
- Docker Compose（一键部署）


快速启动

1. 安装依赖

pip install -r requirements.txt

2. 配置环境变量

创建 .env 文件：

DATABASE_URL=mysql+pymysql://root:密码@localhost:3306/knowledge_base
DASHSCOPE_API_KEY=你的通义千问密钥

3. 初始化数据库

在 MySQL 中创建 knowledge_base 数据库，启动服务后会自动建表。

4. 启动服务

uvicorn main:app --host 127.0.0.1 --port 8001 --reload

访问 http://127.0.0.1:8001/docs 查看 API 文档。


API 接口

POST   /api/users/register         用户注册
POST   /api/users/login            用户登录
POST   /api/users/forgot-password  忘记密码重置
POST   /api/documents/upload       上传文档（需 token）
GET    /api/documents/             文档列表（需 token）
DELETE /api/documents/{id}         删除文档（需 token）
POST   /api/qa/ask                 RAG 智能问答（流式，需 token）
POST   /api/qa/ask-fast            快速问答（工具/技能调用，需 token）
POST   /api/qa/save                保存问答历史（需 token）
GET    /api/qa/history             获取历史记录（需 token）


Docker 部署

docker-compose up -d

服务将在 http://127.0.0.1:8001 启动。


项目结构

knowledge-base-backend/
├── routers/          路由层（API 接口）
├── models/           数据模型层
├── crud/             数据操作层
├── utils/            工具函数（LLM、向量检索、Agent 等）
├── frontend/         前端页面
├── uploads/          文档上传目录
├── main.py           应用入口
├── requirements.txt  依赖列表
├── docker-compose.yml
└── README.md


设计亮点

1. 混合检索

先提取关键词精确匹配文档名，再走向量检索，解决多文档召回不全的问题。

2. 多步检索

第一次检索结果不足时，自动改写问题再查一次，作为兜底召回。

3. 流式与非流式区分

工具调用响应快走非流式，RAG 响应慢走流式输出，优化用户体验。

4. 答案溯源

回答底部强制显示来源文档名，避免模型编造答案。

5. 统一入口

工具调用和技能调用通过 /ask-fast 统一入口，系统自动判断走哪条链路。