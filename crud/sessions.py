#会话管理的数据库操作层，负责会话的增删改查。
from sqlalchemy.orm import Session
from models.sessions import Session as SessionModel
from sqlalchemy.sql import func


def create_session(db: Session, user_id: int, name: str):
    """创建新会话"""
    new_session = SessionModel(user_id=user_id, name=name)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def get_sessions_by_user(db: Session, user_id: int):
    """获取用户的所有会话（按更新时间倒序）"""
    return db.query(SessionModel).filter(SessionModel.user_id == user_id).order_by(SessionModel.updated_at.desc()).all()  #倒序排列


def get_session_by_id(db: Session, session_id: int, user_id: int):
    """获取指定会话（校验用户权限）"""
    return db.query(SessionModel).filter(SessionModel.id == session_id, SessionModel.user_id == user_id).first()


def update_session_name(db: Session, session_id: int, user_id: int, new_name: str):
    """重命名会话"""
    session = get_session_by_id(db, session_id, user_id)
    if not session:
        return None
    session.name = new_name
    session.updated_at = func.now()
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: int, user_id: int):
    """删除会话"""
    session = get_session_by_id(db, session_id, user_id)
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True