import json
import re
from utils.llm_client import call_llm
from utils.skills import SKILLS, list_skills
from utils.multi_agent import multi_agent_task


def should_use_skill(user_question: str) -> bool:
    keywords = ["翻译", "总结", "解释", "这段代码", "什么意思", "告诉我", "是什么", "介绍一下", "翻译并总结",
                "翻译并分析"]
    return any(k in user_question for k in keywords)


def extract_content(question: str, keyword: str) -> str:
    """提取引号内的内容，或去掉关键词后的剩余部分"""
    match = re.search(r'["\'](.*?)["\']', question)
    if match:
        return match.group(1)
    content = question.replace(keyword, "").replace("：", "").replace(":", "").strip()
    return content if content else question


def skill_agent(question: str) -> str:
    if not should_use_skill(question):
        return None

    # 检测多步骤任务
    multi_keywords = ["翻译并总结", "翻译然后总结", "先翻译再总结", "翻译加总结", "translate and summarize"]
    if any(k in question for k in multi_keywords):
        content = extract_content(question, question.split()[0] if question.split() else "")
        return multi_agent_task(content, "translate_summarize")

    if "翻译" in question and "分析" in question:
        content = extract_content(question, "翻译")
        return multi_agent_task(content, "translate_analyze")

    if "翻译" in question:
        content = extract_content(question, "翻译")
        return multi_agent_task(content, "translate")

    if "总结" in question:
        content = extract_content(question, "总结")
        return multi_agent_task(content, "summarize")

    if "分析" in question:
        content = extract_content(question, "分析")
        return multi_agent_task(content, "analyze")

    if "解释" in question or "这段代码" in question:
        content = extract_content(question, "解释")
        return multi_agent_task(content, "analyze")

    return None