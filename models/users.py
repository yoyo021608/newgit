#定义用户表的形状。
from sqlalchemy import Column, Integer, String, DateTime #定义一个列，整数类型，字符串类型，日期时间类型
from sqlalchemy.sql import func
from config.db_conf import Base

class User(Base):
    __tablename__ = "users"  #指定数据库里的表名是 users

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) #整数，主键，索引，自动递增
    username = Column(String(50), unique=True, nullable=False, index=True)#字符串，唯一，不为空，索引
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")#默认值，区分普通用户和管理员。admin 可以查看所有用户的文档，普通用户只能看自己的。
    created_at = Column(DateTime(timezone=True), server_default=func.now())