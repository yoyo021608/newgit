#定义用户相关的 API 请求和响应格式。
from pydantic import BaseModel, EmailStr  #特殊的字符串类型，自动校验邮箱格式
from typing import Optional
from datetime import datetime
#注册请求模型
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
#登录请求模型
class UserLogin(BaseModel):
    username: str
    password: str
#用户响应模型
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True