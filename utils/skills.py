import re


class Skill:
    """技能基类"""
    name = "base"
    description = "基础技能"

    def execute(self, input_text: str) -> str:
        raise NotImplementedError


class TranslateSkill(Skill):
    """翻译技能 - 模拟翻译"""
    name = "translate"
    description = "将中文翻译成英文，或英文翻译成中文"

    def execute(self, input_text: str) -> str:
        # 简单模拟翻译（真实场景可接入翻译API）
        if re.search(r'[\u4e00-\u9fa5]', input_text):
            # 检测到中文，简单模拟英译
            return f"[模拟翻译] {input_text} -> Hello, this is a simulated translation."
        else:
            return f"[模拟翻译] {input_text} -> 你好，这是模拟翻译。"


class SummarizeSkill(Skill):
    """总结技能 - 模拟总结"""
    name = "summarize"
    description = "对文本进行简短总结"

    def execute(self, input_text: str) -> str:
        words = input_text.split()
        if len(words) <= 20:
            return input_text
        return f"[模拟总结] {input_text[:50]}... (共{len(words)}个词)"


class CodeExplainSkill(Skill):
    """代码解释技能"""
    name = "code_explain"
    description = "解释一段代码的作用"

    def execute(self, input_text: str) -> str:
        return f"[模拟代码解释] 这段代码的作用是：{input_text[:30]}... 我理解这是用于处理数据或实现某个功能。"


# 技能注册表
SKILLS = {
    "translate": TranslateSkill(),
    "summarize": SummarizeSkill(),
    "code_explain": CodeExplainSkill()
}


def get_skill(skill_name: str):
    return SKILLS.get(skill_name)


def list_skills():
    return [{"name": s.name, "description": s.description} for s in SKILLS.values()]