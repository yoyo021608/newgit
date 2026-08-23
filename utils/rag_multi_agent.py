"""
RAG Multi-Agent 协作模块
专用于知识库问答场景的多 Agent 协作
"""
from typing import List, Dict, Any
from utils.hybrid_search import hybrid_search
from utils.llm_client import call_llm

#检索 Agent：负责去向量库检索相关内容
class RetrievalAgent:

    def __init__(self):
        self.name = "检索Agent"

    def search(self, query: str, user_id: int, db, top_k: int = 5) -> List[Dict[str, Any]]:
        """执行检索，返回文档列表"""
        results = hybrid_search(query, user_id, db, top_k=top_k)
        return results

#评估 Agent：判断检索结果是否够用、是否相关
class EvaluationAgent:

    def __init__(self):
        self.name = "评估Agent"

    def evaluate(self, results: List[Dict], query: str) -> Dict[str, Any]:
        """
        评估检索结果
        返回: {"need_rewrite": bool, "reason": str, "score": int}
        """
        if not results or len(results) == 0:
            return {
                "need_rewrite": True,
                "reason": "未找到任何相关内容",
                "score": 0
            }

        if len(results) < 2:
            return {
                "need_rewrite": True,
                "reason": f"仅找到 {len(results)} 个结果，信息不足",
                "score": 1
            }

        # 检查结果是否包含问题关键词
        query_keywords = set(query.strip().split())
        matched_count = 0
        for doc in results:
            filename = doc.get("filename", "")
            content = doc.get("content", "")
            text = filename + content
            for kw in query_keywords:
                if kw in text:
                    matched_count += 1
                    break

        if len(query_keywords) > 0 and matched_count < len(query_keywords) * 0.5:
            return {
                "need_rewrite": True,
                "reason": f"检索结果中关键词匹配度不足（{matched_count}/{len(query_keywords)}）",
                "score": 2
            }

        return {
            "need_rewrite": False,
            "reason": "检索结果充足且相关",
            "score": 3
        }

#改写 Agent：当检索结果不足时，改写问题以扩大召回
class RewriteAgent:

    def __init__(self):
        self.name = "改写Agent"

    def rewrite(self, query: str) -> str:
        """调用 LLM 改写问题，使其更宽泛"""
        prompt = f"""
用户原始问题：{query}

请将上面的问题改写成更宽泛、更通用的表达方式，以便检索系统能找到更多相关内容。
直接输出改写后的问题，不要加任何解释或前缀。

示例：
原始：人工智能是什么时候诞生的？
改写：人工智能的历史和起源

原始：勾股定理怎么证明？
改写：勾股定理的相关内容

原始问题：{query}
改写后的问题："""

        try:
            new_query = call_llm(prompt, max_tokens=50)
            new_query = new_query.strip().strip('"').strip("'")
            if not new_query:
                return f"关于{query}的相关内容"
            return new_query
        except Exception:
            return f"关于{query}的相关内容"

#写作 Agent：根据检索结果生成最终回答
class WritingAgent:

    def __init__(self):
        self.name = "写作Agent"

    def write(self, query: str, results: List[Dict]) -> str:
        """基于检索结果生成回答"""
        if not results or len(results) == 0:
            return "未找到相关内容，请尝试换一种问法或上传更多文档。"

        context = ""
        sources = []
        for i, doc in enumerate(results[:5]):
            filename = doc.get("filename", "未知文档")
            content = doc.get("content", "")
            context += f"\n【文档{i + 1}：{filename}】\n{content}\n"
            sources.append(filename)

        sources = list(dict.fromkeys(sources))  #去重并保持顺序

        prompt = f"""
你是一个知识库问答助手。请根据以下文档内容回答用户的问题。

用户问题：{query}

文档内容：
{context}

要求：
1. 基于文档内容回答，不要使用自己的知识编造
2. 如果文档内容不足以回答问题，请明确告知
3. 回答结尾列出引用的文档来源

回答："""

        try:
            answer = call_llm(prompt, max_tokens=500)
            if sources and "来源" not in answer:
                answer += f"\n\n---\n**来源：**\n" + "\n".join([f"- {s}" for s in sources])
            return answer
        except Exception as e:
            return f"生成回答失败：{str(e)}"

#RAG Multi-Agent 协调器：调度各个 Agent 协作完成问答
class RAGMultiAgentCoordinator:

    def __init__(self):
        self.retrieval_agent = RetrievalAgent()
        self.evaluation_agent = EvaluationAgent()
        self.rewrite_agent = RewriteAgent()
        self.writing_agent = WritingAgent()

    def ask(self, query: str, user_id: int, db, max_rewrite_rounds: int = 1) -> Dict[str, Any]:
        """
        执行 Multi-Agent 协作问答
        返回: {"answer": str, "sources": list, "rounds": int, "trace": list}
        """
        trace = []   #记录每个 Agent 的执行过程，用于返回给前端调试
        current_query = query
        all_results = []
        rounds = 0

        # 1. 检索 Agent 执行检索
        trace.append(f"🔍 {self.retrieval_agent.name}：执行检索，查询：{current_query}")
        results = self.retrieval_agent.search(current_query, user_id, db)
        all_results.extend(results)

        # 2. 评估 Agent 评估结果
        eval_result = self.evaluation_agent.evaluate(results, current_query)
        trace.append(f"📊 {self.evaluation_agent.name}：{eval_result['reason']}")

        # 3. 如果需要改写且未超过最大轮数，触发改写 Agent
        while eval_result["need_rewrite"] and rounds < max_rewrite_rounds:
            rounds += 1
            trace.append(f"✏️ {self.rewrite_agent.name}：第{rounds}次改写问题")
            new_query = self.rewrite_agent.rewrite(current_query)
            trace.append(f"   → 改写后：{new_query}")

            trace.append(f"🔍 {self.retrieval_agent.name}：用改写后的问题重新检索")
            new_results = self.retrieval_agent.search(new_query, user_id, db)
            all_results.extend(new_results)

            eval_result = self.evaluation_agent.evaluate(new_results, new_query)
            trace.append(f"📊 {self.evaluation_agent.name}：{eval_result['reason']}")
            current_query = new_query

        # 4. 去重合并结果
        seen_ids = set()
        unique_results = []
        for doc in all_results:
            doc_id = doc.get('doc_id')
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_results.append(doc)

        # 5. 写作 Agent 生成回答
        trace.append(f"✍️ {self.writing_agent.name}：基于 {len(unique_results)} 个文档生成回答")
        answer = self.writing_agent.write(query, unique_results)

        sources = []
        for doc in unique_results[:3]:
            filename = doc.get("filename", "未知文档")
            if filename not in sources:
                sources.append(filename)

        return {
            "answer": answer,
            "sources": sources,
            "rounds": rounds,
            "trace": trace
        }

#RAG Multi-Agent 问答入口
def rag_multi_agent_ask(query: str, user_id: int, db) -> Dict[str, Any]:
    coordinator = RAGMultiAgentCoordinator()
    return coordinator.ask(query, user_id, db)