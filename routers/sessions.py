from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from config.db_conf import get_db
from utils.security import decode_access_token
from crud.sessions import create_session, get_sessions_by_user, get_session_by_id, update_session_name, delete_session
from crud.chat import get_chat_history
from pydantic import BaseModel
from models.chat import ChatHistory

router = APIRouter(prefix="/api/sessions", tags=["会话管理"])


def get_current_user(token: str = Header(...)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的Token")
    return payload.get("user_id")


class SessionCreateRequest(BaseModel):
    name: str


class SessionUpdateRequest(BaseModel):
    name: str


@router.post("/")
def create_new_session(req: SessionCreateRequest, token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    session = create_session(db, user_id, req.name)
    return {"id": session.id, "name": session.name, "created_at": session.created_at}


@router.get("/")
def list_sessions(token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    sessions = get_sessions_by_user(db, user_id)
    return [{"id": s.id, "name": s.name, "created_at": s.created_at, "updated_at": s.updated_at} for s in sessions]


@router.put("/{session_id}")
def rename_session(session_id: int, req: SessionUpdateRequest, token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    session = update_session_name(db, session_id, user_id, req.name)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或无权操作")
    return {"id": session.id, "name": session.name}


@router.delete("/{session_id}")
def delete_session_route(session_id: int, token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    # 删除会话
    if not delete_session(db, session_id, user_id):
        raise HTTPException(status_code=404, detail="会话不存在或无权操作")
    return {"message": "删除成功"}


@router.get("/{session_id}/history")
def get_session_history(session_id: int, token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    # 先验证会话是否属于该用户
    session = get_session_by_id(db, session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或无权操作")
    # 获取该会话的历史记录
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id,
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.created_at.asc()).limit(200).all()
    import json
    result = []
    for h in history:
        sources = []
        if h.sources:
            try:
                sources = json.loads(h.sources)
            except:
                sources = []
        result.append({
            "id": h.id,
            "question": h.question,
            "answer": h.answer,
            "sources": sources,
            "created_at": h.created_at.isoformat() if h.created_at else None
        })
    return result