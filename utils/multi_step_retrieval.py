from utils.hybrid_search import hybrid_search


def multi_step_retrieval(question: str, user_id: int, db, max_steps: int = 2, top_k: int = 15):
    print(f"📚 多步检索第1步: {question}")

    # 第一步：用原问题检索
    step1_results = hybrid_search(question, user_id, db, top_k=top_k)
    print(f"  第1步结果: {len(step1_results)} 个")

    # 如果结果足够，直接返回
    if len(step1_results) >= 2:
        return step1_results

    # 第二步：改写问题，扩大检索
    if max_steps >= 2:
        print("  🔄 结果不足，执行第2步...")
        rewritten = f"关于 {question.split()[0] if question.split() else question} 的相关内容"
        print(f"  改写后: {rewritten}")
        step2_results = hybrid_search(rewritten, user_id, db, top_k=top_k * 2)
        print(f"  第2步结果: {len(step2_results)} 个")

        # 合并去重
        seen = set()
        combined = []
        for r in step1_results + step2_results:
            doc_id = r.get('doc_id')
            if doc_id not in seen:
                seen.add(doc_id)
                combined.append(r)
        return combined

    return step1_results