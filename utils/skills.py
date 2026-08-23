import re
from utils.llm_client import call_llm


class Skill:
    """技能基类"""
    name = "base"
    description = "基础技能"

    def execute(self, input_text: str) -> str:
        raise NotImplementedError


class TranslateSkill(Skill):
    """翻译技能 - 使用通义千问"""
    name = "translate"
    description = "将中文翻译成英文，或英文翻译成中文"

    def execute(self, input_text: str) -> str:
        prompt = f"""请将以下文本翻译成{ '英文' if re.search(r'[\u4e00-\u9fa5]', input_text) else '中文' }。只返回翻译结果，不要添加任何额外说明。

文本：{input_text}"""
        try:
            result = call_llm(prompt)
            return result.strip()
        except Exception as e:
            return f"翻译失败: {str(e)}"


class SummarizeSkill(Skill):
    """总结技能 - 使用通义千问"""
    name = "summarize"
    description = "对文本进行简短总结"

    def execute(self, input_text: str) -> str:
        prompt = f"""请对以下文本进行简洁的总结，提取核心要点。用3-5句话概括，不要超过100字。

文本：{input_text}"""
        try:
            result = call_llm(prompt)
            return result.strip()
        except Exception as e:
            return f"总结失败: {str(e)}"


class CodeExplainSkill(Skill):
    """代码解释技能 - 使用通义千问"""
    name = "code_explain"
    description = "解释一段代码的作用"

    def execute(self, input_text: str) -> str:
        prompt = f"""请解释以下代码的作用。说明代码的功能、输入输出和主要逻辑。

代码：
{input_text}"""
        try:
            result = call_llm(prompt)
            return result.strip()
        except Exception as e:
            return f"代码解释失败: {str(e)}"


# 技能注册表，键是技能名，值是技能实例
SKILLS = {
    "translate": TranslateSkill(),
    "summarize": SummarizeSkill(),
    "code_explain": CodeExplainSkill()
}


def get_skill(skill_name: str):
    return SKILLS.get(skill_name)


def list_skills():
    return [{"name": s.name, "description": s.description} for s in SKILLS.values()]