#用户认证接口。 处理注册、登录、忘记密码三个功能。
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from config.db_conf import get_db
from schemas.users import UserCreate, UserLogin
from crud.users import create_user, authenticate_user, get_user_by_username
from utils.security import create_access_token, hash_password, get_current_user
from models.users import User
from models.sessions import Session as SessionModel
import os
from utils.vector_store import collection

router = APIRouter(prefix="/api/users", tags=["用户"])

class ForgotPasswordRequest(BaseModel):
    username: str
    email: str
    new_password: str


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    new_user = create_user(db, user_data)
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role,
        "created_at": new_user.created_at
    }


@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(data={"sub": str(user.id), "user_id": user.id})
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username, User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户名或邮箱不匹配")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "密码重置成功"}


@router.delete("/me")
def delete_account(
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user)
):
    # 1. 获取该用户的所有文档
    from models.documents import Document
    docs = db.query(Document).filter(Document.user_id == user_id).all()

    # 2. 删除物理文件 + ChromaDB 向量
    for doc in docs:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            print(f"🗑️ 已删除文件: {doc.file_path}")
        try:
            collection.delete(ids=[str(doc.id)])
            print(f"🗑️ 已删除向量: {doc.id}")
        except Exception as e:
            print(f"⚠️ 删除向量失败 {doc.id}: {e}")

    # 3. 先删除该用户的所有会话（解除外键约束）
    db.query(SessionModel).filter(SessionModel.user_id == user_id).delete()

    # 4. 删除用户
    from models.users import User
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        print(f"🗑️ 已注销用户: {user.username}")

    return {"message": "账户已注销"}