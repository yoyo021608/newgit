from sqlalchemy.orm import Session
from models.users import User
from schemas.users import UserCreate
from utils.security import hash_password, verify_password

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

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
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None
    if not verify_password(password, db_user.password_hash):
        return None
    return db_user