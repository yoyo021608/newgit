#定义文档相关的 API 请求和响应格式。
from pydantic import BaseModel
from datetime import datetime
#文档创建请求模型，后端在上传时自己构建
class DocumentCreate(BaseModel):
    filename: str
    file_path: str
    file_type: str
    user_id: int
#文档响应模型
class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_type: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True   #当 routers/documents.py 返回 new_doc（SQLAlchemy 对象）时，FastAPI 会根据 DocumentResponse 的格式自动转换成 JSON，只返回这六个字段。