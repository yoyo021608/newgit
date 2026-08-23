#多步检索工作流
from utils.hybrid_search import hybrid_search
import jieba.analyse


def extract_keywords_for_rewrite(question: str) -> str:
    """提取问题中的核心关键词（用 jieba）"""
    stop_words = {
        "介绍", "什么", "怎么", "为什么", "如何", "哪个", "哪些",
        "多少", "哪里", "区别", "关系", "帮忙", "请问", "一个",
        "一下", "我们", "可以", "应该", "就是", "这个", "那个"
    }
    keywords = jieba.analyse.extract_tags(question, topK=3)  #提取最重要的三个关键词
    filtered = [kw for kw in keywords if kw not in stop_words]
    if not keywords:
        return question
    return " ".join(filtered[:3])


def has_enough_quality(results, threshold: float = 0.6):
    """判断检索结果是否足够好"""
    if not results:
        return False
#没有结果 → 质量不够
    top_score = results[0].get('score', 0)
    if top_score < threshold:
        return False

    if len(results) < 2:
        return False

    return True


def multi_step_retrieval(question: str, user_id: int, db, max_steps: int = 2, top_k: int = 15):
    print(f"📚 多步检索第1步: {question}")

    step1_results = hybrid_search(question, user_id, db, top_k=top_k)
    print(f"  第1步结果: {len(step1_results)} 个")

    if has_enough_quality(step1_results):
        print("  ✅ 结果质量足够，直接返回")
        return step1_results

    if max_steps >= 2:
        print("  🔄 结果不足，执行第2步...")

        keywords = extract_keywords_for_rewrite(question)
        rewritten = f"关于 {keywords} 的相关内容"
        print(f"  改写后: {rewritten}")

        step2_results = hybrid_search(rewritten, user_id, db, top_k=top_k * 2)
        print(f"  第2步结果: {len(step2_results)} 个")

        seen = set()
        combined = []
        for r in step1_results + step2_results:
            doc_id = r.get('doc_id')
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                combined.append(r)
        return combined

    return step1_results