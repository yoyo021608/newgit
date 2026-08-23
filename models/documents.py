#定义文档表结构，文档表的 ORM 模型，记录用户上传文档的元数据
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey #ForeignKey外键，关联到其他表
from sqlalchemy.sql import func
from config.db_conf import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False) #文件扩展名
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) #ForeignKey("users.id") 表示这个文档属于哪个用户。users.id 是用户表的主键
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) #记录文档最后更新时间，用于检测文件是否被修改