#数据库配置文件，管理 MySQL 连接、会话创建和关闭。
from sqlalchemy import create_engine  #创建数据库引擎
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker  #创建会话工厂
import os

# 优先使用环境变量（Docker 部署），否则用本地配置
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:123456@localhost:3306/knowledge_base?charset=utf8mb4")
#创建引擎和会话工厂
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #不自动提交，不自动刷新
Base = declarative_base()
#依赖注入
def get_db():
    db = SessionLocal()  #创建一个数据库会话
    try:
        yield db
    finally:
        db.close()