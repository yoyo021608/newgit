from utils.llm_client import call_llm


class Agent:
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt

    def execute(self, task: str, context: str = "") -> str:
        prompt = f"""{self.system_prompt}

任务：{task}
上下文：{context}

请完成你的任务，只输出结果，不要解释。"""
        return call_llm(prompt)


def multi_agent_task(text: str, task_type: str) -> str:
    """
    多智能体协作执行任务
    task_type: translate, summarize, translate_summarize
    """

    # Agent A：翻译助手
    agent_a = Agent(
        name="翻译助手",
        role="翻译",
        system_prompt="你是一个翻译助手。将输入的中文翻译成英文，或英文翻译成中文。只输出翻译结果。"
    )

    # Agent B：总结助手
    agent_b = Agent(
        name="总结助手",
        role="总结",
        system_prompt="你是一个总结助手。将输入的内容进行简短总结，保留核心信息。只输出总结结果。"
    )

    # Agent C：分析助手
    agent_c = Agent(
        name="分析助手",
        role="分析",
        system_prompt="你是一个分析助手。分析输入内容的要点和关键信息。只输出分析结果。"
    )

    if task_type == "translate":
        return agent_a.execute(text)

    elif task_type == "summarize":
        return agent_b.execute(text)

    elif task_type == "translate_summarize":
        # 先翻译
        translated = agent_a.execute(text)
        # 再总结翻译结果
        summary = agent_b.execute("对以下内容进行总结：" + translated)
        return f"翻译结果：\n{translated}\n\n总结：\n{summary}"

    elif task_type == "analyze":
        return agent_c.execute(text)

    elif task_type == "translate_analyze":
        translated = agent_a.execute(text)
        analysis = agent_c.execute(translated)
        return f"翻译结果：\n{translated}\n\n分析：\n{analysis}"

    else:
        return "未知任务类型"