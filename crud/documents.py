from sqlalchemy.orm import Session
from models.documents import Document
from schemas.documents import DocumentCreate

def create_document(db: Session, doc_data: DocumentCreate):
    db_doc = Document(
        filename=doc_data.filename,
        file_path=doc_data.file_path,
        file_type=doc_data.file_type,
        user_id=doc_data.user_id
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def get_documents_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Document).filter(Document.user_id == user_id).offset(skip).limit(limit).all()

def get_document_by_id(db: Session, doc_id: int, user_id: int):
    return db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()

def delete_document(db: Session, doc_id: int, user_id: int):
    doc = get_document_by_id(db, doc_id, user_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True