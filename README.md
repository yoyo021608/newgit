个人知识库管理系统

基于 FastAPI + ChromaDB + 通义千问 的智能知识库问答系统。


项目简介

用户上传文档后，系统基于文档内容进行智能问答，并显示答案来源。与传统文档管理系统不同，这个项目的核心是"问东西"而不是"存东西"——用户随手丢进去，用一句话就能问出来。


功能

- 用户注册/登录/忘记密码（JWT 认证）
- 注销账户（永久删除用户所有数据，含文档、聊天记录、会话）
- 文档上传/列表/删除（支持 PDF、Word、TXT、Markdown）
- 智能问答（RAG 检索 + 大模型流式回答）
- RAG Multi-Agent 协作问答（检索→评估→改写→写作，四 Agent 协作）
- 快速问答（工具调用：计算/天气/时间/翻译/总结/代码解释）
- 答案溯源（显示答案来源文档）
- 会话管理（新建/重命名/删除/切换会话）
- 历史记录保存与加载（按会话隔离）
- 文档自动更新（修改文件后再次提问自动重新向量化）
- 权限控制（普通用户只能看自己的文档，管理员可看所有文档）


技术栈

- FastAPI + SQLAlchemy + MySQL
- ChromaDB（向量数据库）
- Redis（缓存）
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
SECRET_KEY=你的JWT密钥（可选，默认有占位值）
REDIS_URL=redis://localhost:6379/0（可选，默认值）

3. 初始化数据库

在 MySQL 中创建 knowledge_base 数据库，启动服务后会自动建表。

4. 启动服务

uvicorn main:app --host 127.0.0.1 --port 8001 --reload

访问 http://127.0.0.1:8001/docs 查看 API 文档。


前端页面

启动服务后，双击 frontend/index.html 文件即可打开前端页面。


API 接口

用户认证
POST   /api/users/register         用户注册
POST   /api/users/login            用户登录
POST   /api/users/forgot-password  忘记密码重置
DELETE /api/users/me               注销账户（需 token）

文档管理
POST   /api/documents/upload       上传文档（需 token）
GET    /api/documents/             文档列表（需 token）
DELETE /api/documents/{id}         删除文档（需 token）

会话管理
POST   /api/sessions/              新建会话（需 token）
GET    /api/sessions/              获取会话列表（需 token）
PUT    /api/sessions/{id}          重命名会话（需 token）
DELETE /api/sessions/{id}          删除会话（需 token）
GET    /api/sessions/{id}/history  获取会话历史记录（需 token）

问答
POST   /api/qa/ask                 RAG 智能问答（流式，需 token）
POST   /api/qa/ask-fast            快速问答（工具/技能调用，需 token）
POST   /api/qa/ask-rag-multi-agent RAG Multi-Agent 协作问答（需 token）
POST   /api/qa/save                保存问答历史（需 token）
GET    /api/qa/history             获取全局历史记录（需 token）

MCP 扩展
挂载   /mcp                        MCP 服务（工具调用走 MCP 链路，需 token）


Docker 部署

docker-compose up -d

服务将在 http://127.0.0.1:8001 启动。


项目结构

knowledge-base-backend/
├── routers/          路由层（API 接口）
├── models/           数据模型层
├── crud/             数据操作层
├── utils/            工具函数（LLM、向量检索、Agent、缓存等）
├── frontend/         前端页面
├── uploads/          文档上传目录
├── main.py           应用入口
├── requirements.txt  依赖列表
├── docker-compose.yml
└── README.md


设计亮点

1. 混合检索：精确匹配 + 向量检索

大部分 RAG 项目只做向量检索，但我发现一个问题：用户问"语文、数学、英语"时，向量检索会漏掉部分文档。我改成先精确匹配文档名，再走向量检索，两者结合。这样用户指定查某个文档时能准确定位，模糊搜索时又能靠向量检索兜底。精确匹配权重 10，包含匹配权重 3，按权重排序确保最相关的文档排在前面。

2. 多步检索工作流

第一次检索结果不足时，系统自动改写问题再查一次。这个设计解决了"文档内容太短、向量检索相似度不够"的问题，作为兜底召回。

3. 流式与非流式区分

工具调用和技能调用响应快，走非流式一次性返回；RAG 问答响应慢，走流式逐字输出。让快速响应的功能不卡顿，慢速响应的功能保持流式体验。

4. 答案溯源

回答底部强制显示来源文档名。如果文档里找不到相关内容，系统会明确说"未找到相关内容"，而不是编造答案。

5. 统一入口

用户不需要判断问题该用哪个功能。系统先走快速接口，自动判断是工具调用、技能调用还是 RAG 检索，用户无感知。

6. 工具调用和技能调用

工具调用：计算、天气、时间；技能调用：翻译、总结、代码解释。支持多步骤任务组合，如"翻译并总结"会先翻译再总结。

7. 文档自动更新

用户修改已上传文档的内容后再次提问，系统会自动检测文件修改时间，重新进行向量化，确保回答基于最新内容。无需手动重新上传。

8. 会话管理

每个会话独立保存问答历史，支持新建、重命名（双击会话名）、删除和切换会话。历史记录按会话隔离，切换会话时自动加载对应历史。

9. 注销账户

用户可永久删除账户，系统会级联删除该用户的所有数据：物理文件（uploads/目录）、ChromaDB 向量、文档记录、聊天记录和会话。操作前需输入用户名和密码二次确认。

10. 权限控制

普通用户只能查看和操作自己的文档；管理员（role = 'admin'）可以查看所有用户的文档，便于系统管理。

11. RAG Multi-Agent 协作

把多步检索工作流改造成 Multi-Agent 架构，拆成四个独立的 Agent：检索 Agent 负责查向量库，评估 Agent 判断结果够不够用，改写 Agent 负责改写问题扩大召回，写作 Agent 负责生成最终回答。每个 Agent 职责单一，通过协调器调度协作。

12. Redis 缓存

天气查询每次都要调用第三方 API，有网络延迟。加了 Redis 缓存，同一城市 10 分钟内的查询直接从缓存返回，响应速度明显提升。如果 Redis 连不上，代码会自动降级到直接调用 API，不影响功能使用。


环境变量说明

DATABASE_URL      MySQL 数据库连接字符串（必填）
DASHSCOPE_API_KEY 通义千问 API 密钥（必填）
SECRET_KEY        JWT 签名密钥（可选，默认有占位值）
REDIS_URL         Redis 连接地址（可选，默认 redis://localhost:6379/0）