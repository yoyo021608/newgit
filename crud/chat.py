from sqlalchemy.orm import Session
from models.chat import ChatHistory
import json

def save_chat_history(db: Session, user_id: int, question: str, answer: str, sources: list):
    """保存问答记录"""
    sources_str = json.dumps(sources, ensure_ascii=False) if sources else None
    chat = ChatHistory(
        user_id=user_id,
        question=question,
        answer=answer,
        sources=sources_str
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

def get_chat_history(db: Session, user_id: int, limit: int = 50):
    """获取用户的历史问答记录"""
    return db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id
    ).order_by(ChatHistory.created_at.asc()).limit(limit).all()