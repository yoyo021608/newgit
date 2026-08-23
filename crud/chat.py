#操作聊天记录表的数据。 负责保存问答记录和查询历史记录。
from sqlalchemy.orm import Session
from models.chat import ChatHistory
import json

def save_chat_history(db: Session, user_id: int, question: str, answer: str, sources: list, session_id: int = None):
    sources_str = json.dumps(sources, ensure_ascii=False) if sources else None
    chat = ChatHistory(
        user_id=user_id,
        question=question,
        answer=answer,
        sources=sources_str,
        session_id=session_id
    )
    db.add(chat) #加入会话
    db.commit()  #写入数据库
    db.refresh(chat)
    return chat

def get_chat_history(db: Session, user_id: int, limit: int = 50):
    """获取用户的历史问答记录"""
    return db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id
    ).order_by(ChatHistory.created_at.asc()).limit(limit).all()  #按时间升序排列，最多返回limit条，返回所有匹配结果