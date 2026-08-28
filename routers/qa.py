#智能问答的核心路由，快速问答、RAG 流式问答、历史记录保存和查询四个接口。
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
import jieba
import jieba.posseg #词性标注
import os
from datetime import datetime
from utils.file_reader import read_file

router = APIRouter(prefix="/api/qa", tags=["智能问答"])

class AskRequest(BaseModel):
    question: str
    session_id: int = None  # 关联会话

class SaveRequest(BaseModel):
    question: str
    answer: str
    sources: list = []

def get_current_user(token: str = Header(...)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的Token")
    return payload.get("user_id")

#关键词提取
def extract_keywords(question: str):
    words = jieba.posseg.cut(question)
    result = []
    for word, flag in words:
        if flag.startswith('n') or flag.startswith('v'):
            if len(word) >= 2:
                result.append(word)
    if not result:
        words = re.findall(r'[\u4e00-\u9fa5]+', question)
        for w in words:
            if len(w) >= 4:
                for i in range(0, len(w), 2):
                    if i + 1 < len(w):
                        result.append(w[i:i + 2])
            else:
                if len(w) >= 2:
                    result.append(w)
    seen = set()
    unique = []
    for w in result:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    print(f"🔍 提取关键词: {unique}")
    return unique


def multi_keyword_search(question: str, user_id: int, db: Session):
    from models.documents import Document
    from utils.vector_store import update_document_in_vector_store

    STOP_WORDS = {
        "介绍", "一下", "什么", "怎么", "为什么", "如何", "和数", "学有",
        "区别", "关系", "帮忙", "请问", "一个", "我们", "可以", "应该",
        "就是", "这个", "那个", "一些", "已经", "可能", "因为", "所以",
        "但是", "如果", "然后", "这样", "那样", "非常", "比较"
    }

    keywords = extract_keywords(question)
    keywords = [kw for kw in keywords if kw not in STOP_WORDS]
    print(f"🔍 关键词(过滤后): {keywords}")

    if not keywords:
        return multi_step_retrieval(question, user_id, db, max_steps=2, top_k=15)

    all_docs = db.query(Document).filter(Document.user_id == user_id).all()
    print(f"📁 用户文档: {[d.filename for d in all_docs]}")

    results = []
    matched_ids = []

    for kw in keywords:
        # 先收集所有匹配的文档
        matched_docs = []
        for doc in all_docs:
            if kw in doc.filename and doc.id not in matched_ids:
                filename_without_ext = doc.filename.rsplit('.', 1)[0] if '.' in doc.filename else doc.filename
                if filename_without_ext == kw:
                    match_type = "exact"
                else:
                    match_type = "contain"
                matched_docs.append((doc, match_type))

        # 按匹配类型排序：精确匹配在前
        matched_docs.sort(key=lambda x: 0 if x[1] == "exact" else 1)

        for doc, match_type in matched_docs:
            file_path = doc.file_path
            content = ""
            try:
                if os.path.exists(file_path):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))  #获取文件最后修改时间（时间戳）
                    print(f"🔍 检查文件: {doc.filename}, file_mtime={file_mtime}, updated_at={doc.updated_at}")
                    if not doc.updated_at or file_mtime > doc.updated_at.replace(tzinfo=None):
                        print(f"🔄 文件 {doc.filename} 已修改，更新向量库...")
                        content = read_file(file_path)
                        update_document_in_vector_store(
                            doc.id,
                            content,
                            {'filename': doc.filename, 'user_id': user_id}
                        )
                        doc.updated_at = file_mtime
                        db.commit()
                        print(f"✅ 文档 {doc.filename} 向量库已更新")
                    else:
                        content = read_file(file_path)
                else:
                    print(f"⚠️ 文件不存在: {file_path}")
            except Exception as e:
                print(f"⚠️ 读取文档 {doc.filename} 失败: {e}")
                content = ""

            if match_type == "exact":
                weight = 10
            else:
                weight = 3

            matched_ids.append(doc.id)
            results.append({
                'doc_id': doc.id,
                'filename': doc.filename,
                'content': content,
                'weight': weight
            })
            print(f"  ✅ 关键词 '{kw}' 匹配到: {doc.filename} (权重: {weight})")

    if not results:
        print("  ⚠️ 精确匹配失败，走向量检索...")
        return multi_step_retrieval(question, user_id, db, max_steps=2, top_k=15)

    # 按权重降序排序，权重相同按文件名长度升序（更短的文件名排在前面）
    results.sort(key=lambda x: (x.get('weight', 0), -len(x.get('filename', ''))), reverse=True)  #权重相同时，文件名短的排前面

    final_results = []
    for idx, r in enumerate(results):
        final_results.append({
            'doc_id': r['doc_id'],
            'filename': r['filename'],
            'content': r['content'],
            'weight': r['weight'],
            'rank': idx + 1
        })

    print(f"🔍 共匹配 {len(final_results)} 个文档（按权重排序）")
    for r in final_results:
        print(f"  📄 #{r['rank']} {r['filename']} (权重: {r['weight']})")

    # 如果结果太少（少于2个），触发多步检索兜底
    if len(final_results) < 2:
        print(f"  ⚠️ 精确匹配结果太少（{len(final_results)}个），触发多步检索兜底...")
        vector_results = multi_step_retrieval(question, user_id, db, max_steps=2, top_k=15)
        # 合并结果，去重
        existing_ids = {r['doc_id'] for r in final_results}
        for r in vector_results:
            if r['doc_id'] not in existing_ids:
                # 给向量检索结果一个较低的权重
                r['weight'] = r.get('weight', 1)
                final_results.append(r)
        # 重新按权重排序
        final_results.sort(key=lambda x: x.get('weight', 0), reverse=True)
        # 重新编号
        for idx, r in enumerate(final_results):
            r['rank'] = idx + 1
        print(f"🔍 合并后共 {len(final_results)} 个文档")
        for r in final_results:
            print(f"  📄 #{r['rank']} {r['filename']} (权重: {r['weight']})")

    return final_results


@router.post("/ask-fast")
def ask_fast(req: AskRequest, token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    question = req.question
    session_id = req.session_id  # 新增：获取 session_id

    tool_result = tool_agent(question)
    if tool_result:
        try:
            save_chat_history(db, user_id, question, tool_result, [], session_id)
            print(f"✅ 快速问答历史已保存: {question}")
        except Exception as e:
            print(f"❌ 保存聊天记录失败: {e}")
        return {"answer": f"🔧 {tool_result}"}

    skill_result = skill_agent(question)
    if skill_result:
        try:
            save_chat_history(db, user_id, question, skill_result, [], session_id)
            print(f"✅ 快速问答历史已保存: {question}")
        except Exception as e:
            print(f"❌ 保存聊天记录失败: {e}")
        return {"answer": f"🧠 {skill_result}"}

    return {"answer": None}

#RAG流式生成
def generate_stream(question: str, user_id: int, db: Session, session_id: int = None):
    print(f"📝 收到问题: {question}")
    results = multi_keyword_search(question, user_id, db)

    if not results:
        yield "未找到相关内容，请上传文档后再提问。"
        return

    contexts = [r['content'] for r in results]
    sources = [{'content': r['content'], 'filename': r['filename'], 'doc_id': r['doc_id']} for r in results]
    context_text = "\n\n".join([f"【文档{i + 1}: {sources[i]['filename']}】\n{ctx}" for i, ctx in enumerate(contexts)])

    print(f"📄 文档顺序（按权重排序）:")
    for i, r in enumerate(results):
        print(f"  文档{i + 1}: {r['filename']} (权重: {r.get('weight', 'N/A')})")
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
        save_chat_history(db, user_id, question, full_answer, sources, session_id)
    except Exception as e:
        print(f"保存聊天记录失败: {e}")

    yield "\n\n---\n**来源：**\n"
    seen_sources = set()
    for s in sources:
        if s['filename'] not in seen_sources:
            seen_sources.add(s['filename'])
            yield f"- {s['filename']}\n"


@router.post("/ask")
def ask_question(req: AskRequest, token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    return StreamingResponse(
        generate_stream(req.question, user_id, db, req.session_id),
        media_type="text/plain"
    )


@router.post("/save")
def save_chat(req: SaveRequest, token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    try:
        save_chat_history(db, user_id, req.question, req.answer, req.sources)
        return {"message": "保存成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/history")
def get_history(token: str = Header(...), db: Session = Depends(get_db)):
    user_id = get_current_user(token)
    history = get_chat_history(db, user_id, limit=200)
    result = []
    for h in history:
        sources = []
        if h.sources:
            try:
                sources = json.loads(h.sources)  #把 JSON 字符串解析回列表
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


#RAG Multi-Agent 问答接口
@router.post("/ask-rag-multi-agent")
def ask_rag_multi_agent(req: AskRequest, token: str = Header(...), db: Session = Depends(get_db)):
    """
    RAG Multi-Agent 协作问答接口
    多个 Agent 协作完成一次问答：检索 → 评估 → 改写（如需）→ 写作
    """
    user_id = get_current_user(token)
    from utils.rag_multi_agent import rag_multi_agent_ask
    from crud.chat import save_chat_history

    question = req.question
    session_id = req.session_id

    # 执行 RAG Multi-Agent 问答
    result = rag_multi_agent_ask(question, user_id, db)

    # 保存历史记录
    try:
        save_chat_history(db, user_id, question, result["answer"], result["sources"], session_id)
        print(f"✅ RAG Multi-Agent 问答历史已保存: {question}")
    except Exception as e:
        print(f"❌ 保存聊天记录失败: {e}")

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "rounds": result["rounds"],
        "trace": result["trace"]
    }