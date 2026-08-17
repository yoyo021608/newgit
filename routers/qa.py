from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config.db_conf import get_db
from utils.multi_step_retrieval import multi_step_retrieval
from utils.llm_client import call_llm_stream
from utils.security import decode_access_token
from utils.tool_agent import tool_agent
from utils.skill_agent import skill_agent
from crud.chat import save_chat_history, get_chat_history
import re
import json

router = APIRouter(prefix="/api/qa", tags=["智能问答"])


class AskRequest(BaseModel):
    question: str


class SaveRequest(BaseModel):
    question: str
    answer: str
    sources: list = []


def get_current_user(token: str = Header(...)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的Token")
    return payload.get("user_id")


def extract_keywords(question: str):
    # 提取所有连续中文
    words = re.findall(r'[\u4e00-\u9fa5]+', question)

    result = []
    for w in words:
        if len(w) >= 4:
            # 按2字拆分
            for i in range(0, len(w), 2):
                if i + 1 < len(w):
                    result.append(w[i:i + 2])
        else:
            result.append(w)

    # 去重
    seen = set()
    unique = []
    for w in result:
        if w not in seen and len(w) >= 2:
            seen.add(w)
            unique.append(w)

    return unique


def multi_keyword_search(question: str, user_id: int, db: Session):
    keywords = extract_keywords(question)
    print(f"🔍 提取关键词: {keywords}")

    if not keywords:
        return multi_step_retrieval(question, user_id, db, max_steps=2, top_k=15)

    from models.documents import Document
    all_docs = db.query(Document).filter(Document.user_id == user_id).all()
    print(f"📁 用户文档: {[d.filename for d in all_docs]}")

    results = []
    matched_ids = []

    for kw in keywords:
        for doc in all_docs:
            if kw in doc.filename and doc.id not in matched_ids:
                matched_ids.append(doc.id)
                try:
                    with open(doc.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    content = ""
                results.append({
                    'doc_id': doc.id,
                    'filename': doc.filename,
                    'content': content,
                    'score': 1.0
                })
                print(f"  ✅ 关键词 '{kw}' 匹配到: {doc.filename}")
                break

    # 如果文件名匹配不到任何文档，走向量检索
    if not results:
        print("  ⚠️ 文件名匹配不到，走向量检索...")
        return multi_step_retrieval(question, user_id, db, max_steps=2, top_k=15)

    print(f"🔍 共匹配 {len(results)} 个文档")
    return results


@router.post("/ask-fast")
def ask_fast(
        req: AskRequest,
        token: str = Header(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user(token)
    question = req.question

    # 工具调用
    tool_result = tool_agent(question)
    if tool_result:
        try:
            save_chat_history(db, user_id, question, tool_result, [])
        except Exception as e:
            print(f"保存聊天记录失败: {e}")
        return {"answer": f"🔧 {tool_result}"}

    # 技能调用
    skill_result = skill_agent(question)
    if skill_result:
        try:
            save_chat_history(db, user_id, question, skill_result, [])
        except Exception as e:
            print(f"保存聊天记录失败: {e}")
        return {"answer": f"🧠 {skill_result}"}

    return {"answer": None}


def generate_stream(question: str, user_id: int, db: Session):
    print(f"📝 收到问题: {question}")

    # RAG 问答 - 流式输出
    print("📚 进入 RAG 检索...")
    results = multi_keyword_search(question, user_id, db)

    if not results:
        yield "未找到相关内容，请上传文档后再提问。"
        return

    keywords = extract_keywords(question)
    if keywords:
        weighted_results = []
        for r in results:
            filename = r.get('filename', '')
            content = r.get('content', '')
            weight = 0
            for kw in keywords:
                if kw in filename:
                    weight += 3
                elif kw in content:
                    weight += 1
            r['weight'] = weight
            weighted_results.append(r)
        weighted_results.sort(key=lambda x: (x.get('weight', 0), x.get('score', 0)), reverse=True)
        results = weighted_results

    contexts = [r['content'] for r in results]
    sources = [{'content': r['content'], 'filename': r['filename'], 'doc_id': r['doc_id']} for r in results]
    context_text = "\n\n".join([f"【文档{i + 1}: {sources[i]['filename']}】\n{ctx}" for i, ctx in enumerate(contexts)])

    prompt = f"""请根据以下文档内容回答用户的问题。**文档1是与用户问题最相关的文档，请优先使用文档1的内容回答。**

    文档内容：
    {context_text}

    用户问题：{question}

    要求：
    1. **优先使用文档1的内容**回答用户问题
    2. 如果文档1中找不到答案，再使用其他文档补充
    3. 回答要简洁准确，不要编造文档中没有的内容
    4. 在最后列出引用的来源文档"""

    full_answer = ""
    for chunk in call_llm_stream(prompt):
        full_answer += chunk
        yield chunk

    try:
        save_chat_history(db, user_id, question, full_answer, sources)
    except Exception as e:
        print(f"保存聊天记录失败: {e}")

    yield "\n\n---\n**来源：**\n"
    seen_sources = set()
    for s in sources:
        if s['filename'] not in seen_sources:
            seen_sources.add(s['filename'])
            yield f"- {s['filename']}\n"


@router.post("/ask")
def ask_question(
        req: AskRequest,
        token: str = Header(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user(token)
    return StreamingResponse(
        generate_stream(req.question, user_id, db),
        media_type="text/plain"
    )


@router.get("/history")
def get_history(
        token: str = Header(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user(token)
    history = get_chat_history(db, user_id, limit=50)
    result = []
    for h in history:
        sources = []
        if h.sources:
            try:
                sources = json.loads(h.sources)
            except:
                sources = []
        result.append({
            "id": h.id,
            "question": h.question,
            "answer": h.answer,
            "sources": sources,
            "created_at": h.created_at.isoformat() if h.created_at else None
        })
    return result