#操作用户表的数据。负责对 users 表的增删改查（CRUD），包括：查用户、创建用户、验证用户登录。
from sqlalchemy.orm import Session
from models.users import User
from schemas.users import UserCreate
from utils.security import hash_password, verify_password

def get_user_by_username(db: Session, username: str):   #db: Session	数据库会话，从路由层传进来
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()   #db.query(User)	查 users 表

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user_data: UserCreate):
    hashed = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed,
        role="user"
    )
    db.add(db_user)  #把对象加入会话，还没真正存
    db.commit()   #真正执行 SQL，把数据存到 MySQL
    db.refresh(db_user)    #从 MySQL 重新读取，拿到自动生成的 id 和 created_at
    return db_user
#验证用户登录
def authenticate_user(db: Session, username: str, password: str):
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None
    if not verify_password(password, db_user.password_hash):
        return None
    return db_user