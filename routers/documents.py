#文档管理的 API 接口。 提供三个功能：上传文档、查看文档列表、删除文档。
import os  #检查文件是否存在、拼接路径
import shutil  #把上传的文件流复制到硬盘
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header  #UploadFile, File接收前端传过来的文件；Header从 HTTP 请求头中取 token
from sqlalchemy.orm import Session  #SQLAlchemy 数据库会话类型
from config.db_conf import get_db
from crud.documents import create_document, get_documents_by_user, get_document_by_id, delete_document
from schemas.documents import DocumentCreate, DocumentResponse  #定义请求格式和响应格式
from utils.security import decode_access_token  #解密 JWT token
from utils.file_reader import read_file
from utils.vector_store import add_document_to_vector_store, collection  #操作 ChromaDB 向量库
from crud.users import get_user_by_id
from models.documents import Document

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

UPLOAD_DIR = "uploads"  #定义文件存哪里
os.makedirs(UPLOAD_DIR, exist_ok=True)  #如果 uploads/ 文件夹不存在，自动创建。exist_ok=True 表示如果已经存在也不报错

#获取当前用户id
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
#校验文件类型
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "docx", "txt", "md"]:
        raise HTTPException(status_code=400, detail="不支持的文件类型，请上传 PDF、Word、TXT 或 MD 文件")

    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")  #拼接路径
    with open(file_path, "wb") as f:   #以二进制写入模式打开
        shutil.copyfileobj(file.file, f)  #把上传的文件流复制到本地硬盘

    file_content = read_file(file_path)
    #在 MySQL 中创建文档记录
    doc_data = DocumentCreate(   #数据校验
        filename=file.filename,
        file_path=file_path,
        file_type=ext,
        user_id=user_id
    )
    new_doc = create_document(db, doc_data)
    #存入 ChromaDB 向量库
    add_document_to_vector_store(
        doc_id=new_doc.id,
        content=file_content,
        metadata={"filename": file.filename, "user_id": user_id}
    )

    return new_doc
#new_doc 是一个 SQLAlchemy 对象，FastAPI 会根据 response_model=DocumentResponse 自动转换成 JSON：

@router.get("/", response_model=list[DocumentResponse])     #返回的数据格式是 DocumentResponse 的列表（数组）
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
        collection.delete(ids=[str(doc_id)])  #从 ChromaDB 删除 ID 为 doc_id 的向量，ChromaDB 的 ids 参数要求字符串类型，而 doc_id 是整数
        print(f"✅ 向量库中已删除文档 {doc_id}")
    except Exception as e:
        print(f"⚠️ 向量库删除失败: {e}")
    #删除物理文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    #删除 MySQL 记录
    delete_document(db, doc_id, user_id)
    return {"message": "文档已删除"}