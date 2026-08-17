import re
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session
from models.documents import Document
from utils.vector_store import search_similar


def tokenize(text: str):
    """简单分词，用于 BM25"""
    # 按非字母数字字符分割，转小写
    return re.findall(r'\w+', text.lower())


def bm25_search(query: str, documents_texts: list, top_k: int = 3):
    """
    对给定的文档列表进行 BM25 检索
    documents_texts: list of str, 每个元素是一篇文档的内容
    返回: list of (index, score)
    """
    if not documents_texts:
        return []
    # 分词
    tokenized_docs = [tokenize(doc) for doc in documents_texts]
    bm25 = BM25Okapi(tokenized_docs)
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)
    # 取 top_k
    scored = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def hybrid_search(query: str, user_id: int, db: Session, top_k: int = 5):
    """
    混合检索：向量检索 + BM25 关键词检索
    返回：合并去重后的结果列表
    """
    # 1. 向量检索
    vector_results = search_similar(query, top_k=top_k * 2)

    # 2. 获取该用户的所有文档内容（用于 BM25）
    docs = db.query(Document).filter(Document.user_id == user_id).all()
    doc_texts = []
    doc_metas = []
    for doc in docs:
        try:
            with open(doc.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                doc_texts.append(content)
                doc_metas.append({
                    'id': doc.id,
                    'filename': doc.filename,
                    'file_path': doc.file_path
                })
        except:
            continue

    if not doc_texts:
        # 没有文档时只返回向量结果
        return format_vector_results(vector_results, doc_metas)

    # 3. BM25 检索
    bm25_results = bm25_search(query, doc_texts, top_k=top_k * 2)

    # 4. 合并结果（去重，按综合分数排序）
    # 这里简单实现：向量结果和 BM25 结果各取一半，合并去重
    combined = []
    seen_ids = set()

    # 向量结果优先
    vec_items = format_vector_results(vector_results, doc_metas)
    for item in vec_items:
        if item['doc_id'] not in seen_ids:
            combined.append(item)
            seen_ids.add(item['doc_id'])

    # BM25 结果补充
    for idx, score in bm25_results:
        if idx < len(doc_metas):
            doc_id = doc_metas[idx]['id']
            if doc_id not in seen_ids:
                combined.append({
                    'doc_id': doc_id,
                    'filename': doc_metas[idx]['filename'],
                    'content': doc_texts[idx][:300] + '...',
                    'score': float(score)
                })
                seen_ids.add(doc_id)

    return combined[:top_k]


def format_vector_results(vector_results, doc_metas):
    """将向量检索结果格式化为统一格式"""
    items = []
    if not vector_results or not vector_results['documents']:
        return items
    docs = vector_results['documents'][0]
    metas = vector_results['metadatas'][0]
    distances = vector_results['distances'][0] if 'distances' in vector_results else []
    for i, (content, meta) in enumerate(zip(docs, metas)):
        items.append({
            'doc_id': meta.get('doc_id', 0),
            'filename': meta.get('filename', '未知文档'),
            'content': content[:300] + '...',
            'score': float(1 - distances[i]) if distances else 0.5
        })
    return items