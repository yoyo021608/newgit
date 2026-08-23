#操作文档表数据
from sqlalchemy.orm import Session
from models.documents import Document
from schemas.documents import DocumentCreate
#创建文档记录，只负责在 MySQL 里插入一条记录，不负责保存文件内容。
def create_document(db: Session, doc_data: DocumentCreate):
    db_doc = Document(
        filename=doc_data.filename,
        file_path=doc_data.file_path,
        file_type=doc_data.file_type,
        user_id=doc_data.user_id,
        # 不设置 updated_at，让数据库自动填充
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def get_documents_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Document).filter(Document.user_id == user_id).offset(skip).limit(limit).all()  #分页，跳过前 N 条，最多返回N条

def get_document_by_id(db: Session, doc_id: int, user_id: int):
    return db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()

def delete_document(db: Session, doc_id: int, user_id: int):
    doc = get_document_by_id(db, doc_id, user_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True