#定义聊天记录表的结构
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey #Text长文本类型，比 String 容量大，适合存问题和答案
from sqlalchemy.sql import func
from config.db_conf import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # 存 JSON 字符串（来源简单，不需要建表），可以为空
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(Integer, nullable=True)