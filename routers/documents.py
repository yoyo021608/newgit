import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header
from sqlalchemy.orm import Session
from config.db_conf import get_db
from crud.documents import create_document, get_documents_by_user, get_document_by_id, delete_document
from schemas.documents import DocumentCreate, DocumentResponse
from utils.security import decode_access_token
from utils.file_reader import read_file
from utils.vector_store import add_document_to_vector_store, collection
from crud.users import get_user_by_id
from models.documents import Document

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_current_user(token: str = Header(...)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的Token")
    return payload.get("user_id")


def get_current_user_role(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    return user.role if user else "user"


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
        file: UploadFile = File(...),
        token: str = Header(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user(token)

    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "docx", "txt", "md"]:
        raise HTTPException(status_code=400, detail="不支持的文件类型，请上传 PDF、Word、TXT 或 MD 文件")

    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_content = read_file(file_path)

    doc_data = DocumentCreate(
        filename=file.filename,
        file_path=file_path,
        file_type=ext,
        user_id=user_id
    )
    new_doc = create_document(db, doc_data)

    add_document_to_vector_store(
        doc_id=new_doc.id,
        content=file_content,
        metadata={"filename": file.filename, "user_id": user_id}
    )

    return new_doc


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
        skip: int = 0,
        limit: int = 100,
        token: str = Header(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user(token)
    role = get_current_user_role(db, user_id)

    if role == "admin":
        docs = db.query(Document).offset(skip).limit(limit).all()
    else:
        docs = db.query(Document).filter(Document.user_id == user_id).offset(skip).limit(limit).all()

    return docs


@router.delete("/{doc_id}")
def delete_document_route(
        doc_id: int,
        token: str = Header(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user(token)
    role = get_current_user_role(db, user_id)

    if role == "admin":
        doc = db.query(Document).filter(Document.id == doc_id).first()
    else:
        doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 删除向量库中的数据
    try:
        collection.delete(ids=[str(doc_id)])
        print(f"✅ 向量库中已删除文档 {doc_id}")
    except Exception as e:
        print(f"⚠️ 向量库删除失败: {e}")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    delete_document(db, doc_id, user_id)
    return {"message": "文档已删除"}