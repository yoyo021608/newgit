from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import os
from fastapi import HTTPException, Header, status
from typing import Optional

# 从环境变量读取 SECRET_KEY，如果没有则使用默认值（仅开发环境）
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希加密"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配哈希值"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """生成 JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    """解析 JWT token，失败返回 None"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None


# ========== 获取当前用户（依赖注入） ==========
def get_current_user(token: str = Header(...)):
    """
    从请求头获取 token，解码后返回用户 ID
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的Token")

    # 从 user_id 字段取用户 ID
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token中缺少用户ID")

    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="用户ID格式无效")