class BaseAgent:
    """所有 Agent 的基类。

    每个 Agent 都遵循统一协议：
      1. _build_context: 从共享状态读取上游 Agent 的产出（消息互通）
      2. _build_prompt:   组装发给 LLM 的提示词
      3. run:             调用 LLM（或 mock），并把结果 publish 回共享状态
    """

    def __init__(self, name, system, output_key, llm):
        self.name = name
        self.system = system
        self.output_key = output_key
        self.llm = llm

    def _build_context(self, state):
        raise NotImplementedError

    def _build_prompt(self, context):
        raise NotImplementedError

    def _mock(self, prompt, context):
        raise NotImplementedError

    def run(self, state):
        context = self._build_context(state)
        prompt = self._build_prompt(context)
        raw = None
        try:
            raw = self.llm.chat(self.system, prompt)
        except Exception as e:  # noqa: BLE001
            # 真实引擎调用失败时，降级为 mock 模板输出，保证流程不中断
            print(f"    [警告] {self.name} 真实模型调用失败，已降级为 mock 模板: {e}")
        # mock 模式下 LLM 返回 None，由 Agent 自身的 _mock 产出可读示例
        if raw is None:
            raw = self._mock(prompt, context)
        state.publish(self.output_key, raw, self.name)
        return raw


class RequirementAgent(BaseAgent):
    """需求 Agent：接收用户的产品需求描述，输出标准化软件需求文档。无上游依赖。"""

    def __init__(self, llm):
        super().__init__(
            name="需求Agent",
            system=(
                "你是一名资深软件需求分析师。"
                "请对用户提供的产品需求描述做标准化整理，输出结构化软件需求文档"
                "（功能需求、非功能需求、验收标准）。"
            ),
            output_key="requirement",
            llm=llm,
        )

    def _build_context(self, state):
        return {"user_requirement": state.read("user_requirement")}

    def _build_prompt(self, context):
        return (
            "请对用户提供的产品需求描述做标准化整理，输出需求文档：\n"
            f"{context['user_requirement']}"
        )

    def _mock(self, prompt, context):
        req = context["user_requirement"]
        return f"""# 标准化软件需求文档
## 原始需求（用户输入）
{req}

## 功能需求
1. 系统应支持核心业务的创建、查询与管理。
2. 提供清晰的列表与详情视图。
3. 支持基础的增删改查操作。

## 非功能需求
- 接口平均响应时间 < 200ms
- 支持 ≥ 100 并发用户
- 数据持久化存储

## 验收标准
- 上述功能可在演示中端到端完整跑通。
"""


class DesignAgent(BaseAgent):
    """设计 Agent：基于需求文档产出技术设计（模块/接口/数据流）。"""

    def __init__(self, llm):
        super().__init__(
            name="设计Agent",
            system=(
                "你是一名软件架构师。"
                "请基于需求文档输出技术设计：模块划分、核心接口、数据流。"
            ),
            output_key="design",
            llm=llm,
        )

    def _build_context(self, state):
        return {"requirement": state.read("requirement")}

    def _build_prompt(self, context):
        return f"需求如下：\n{context['requirement']}\n\n请输出技术设计。"

    def _mock(self, prompt, context):
        requirement = context["requirement"]
        # 引用上游需求文档内容，作为「读取了需求 Agent 产物」的互通证据
        return f"""# 技术设计文档
## 依据需求（节选）
{requirement[:60]}...

## 模块划分
- api 层：接收 HTTP 请求，参数校验
- service 层：核心业务逻辑
- storage 层：数据持久化

## 核心接口
- POST   /tasks          创建任务
- GET    /tasks          列出任务
- GET    /tasks/{{id}}   查询详情

## 数据流
用户请求 -> api 层 -> service 层 -> storage 层 -> 返回结果
"""


class CodingAgent(BaseAgent):
    """编码 Agent：基于技术设计产出可运行的 Python 代码骨架。"""

    def __init__(self, llm):
        super().__init__(
            name="编码Agent",
            system=(
                "你是一名后端工程师。"
                "请基于技术设计输出可运行的 Python 代码骨架（含关键函数与注释）。"
            ),
            output_key="code",
            llm=llm,
        )

    def _build_context(self, state):
        return {
            "requirement": state.read("requirement"),
            "design": state.read("design"),
        }

    def _build_prompt(self, context):
        return (
            "技术设计如下：\n"
            f"{context['design']}\n\n"
            "请输出一个精简、可运行的 Python 代码骨架（建议 50-80 行以内，"
            "聚焦核心类与 2-3 个关键函数及注释，无需完整实现所有细节）。"
        )

    def _mock(self, prompt, context):
        design = context["design"]
        # 关键：编码产物显式引用「设计 Agent」产出的内容（单行化，避免破坏代码注释）
        # 与分层/接口(/tasks)，以此作为「读取了上游设计产物」的互通证据。
        design_excerpt = design.replace("\n", " ")[:80]
        return (
            '# -*- coding: utf-8 -*-\n'
            '"""最小可运行骨架（依据设计 Agent 产出实现）"""\n\n'
            f"# 依据设计 Agent 产出（节选）：{design_excerpt}...\n\n"
            "# 模块划分 api / service / storage，接口 /tasks\n\n"
            "class StorageLayer:\n"
            "    def __init__(self):\n"
            "        self._items = {}\n\n"
            "    def save(self, task_id, payload):\n"
            "        self._items[task_id] = payload\n"
            "        return task_id\n\n"
            "    def list_all(self):\n"
            "        return list(self._items.values())\n\n"
            "    def get(self, task_id):\n"
            "        return self._items.get(task_id)\n\n"
            "class ServiceLayer:\n"
            "    def __init__(self, storage):\n"
            "        self.storage = storage\n\n"
            "    def create_task(self, payload):\n"
            "        return self.storage.save(id(payload), payload)\n\n"
            "class ApiLayer:\n"
            "    def __init__(self):\n"
            "        self.service = ServiceLayer(StorageLayer())\n\n"
            "    def create(self, payload):        # POST   /tasks\n"
            "        return self.service.create_task(payload)\n\n"
            "    def list_tasks(self):             # GET    /tasks\n"
            "        return self.service.storage.list_all()\n\n"
            'if __name__ == "__main__":\n'
            "    api = ApiLayer()\n"
            '    print(api.create({"title": "示例任务"}))\n'
        )
