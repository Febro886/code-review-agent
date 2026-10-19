class Workflow:
    """顺序执行的简单 Workflow 编排。

    满足 PPT「技术要求」中的基本流程控制（顺序执行）：
    需求 Agent -> 设计 Agent -> 编码 Agent，
    每个 Agent 通过共享状态接收上游产物、写入自身产物，实现 Agent 间信息互通。
    """

    # 各 Agent 产出对应的落盘文件名（用于预览时提示完整路径）
    _OUTPUT_FILES = {
        "requirement": "output/requirement.md",
        "design": "output/design.md",
        "code": "output/code.py",
    }

    def __init__(self, agents, state):
        self.agents = agents
        self.state = state

    def run(self, initial_requirement):
        print("=" * 60)
        print("Workflow 启动：Mini SE 流程（需求 -> 设计 -> 代码）")
        print("-" * 60)
        print("参与协作的 3 个 Agent：")
        role_map = {
            "需求Agent": "将用户需求标准化为软件需求文档",
            "设计Agent": "基于需求产出技术设计（模块 / 接口 / 数据流）",
            "编码Agent": "基于设计产出可运行代码骨架",
        }
        for i, agent in enumerate(self.agents, 1):
            engine = getattr(agent.llm, "label", None) or f"{agent.llm.provider} / {agent.llm.model or 'mock'}"
            role = role_map.get(agent.name, "")
            print(f"  {i}. {agent.name} —— 职责：{role}")
            print(f"     所用引擎：{engine}")
        print("=" * 60)

        # 用户作为流程起点，将「产品需求描述」写入共享状态
        self.state.publish("user_requirement", initial_requirement, "User")

        for agent in self.agents:
            engine = getattr(agent.llm, "label", None) or f"{agent.llm.provider} / {agent.llm.model or 'mock'}"
            print(f"\n>>> 步骤：运行 {agent.name}（引擎：{engine}）")
            print(f"    {agent.name} 正在分析上游信息并生成产出 ...")
            agent.run(self.state)
            # 直接在终端完整打印该 Agent 的产出，便于查看（不落盘保存）
            content = self.state.read(agent.output_key)
            lines = content.strip().splitlines()
            print(f"    ── {agent.name} 完整产出（共 {len(lines)} 行）──")
            for ln in lines:
                print("      " + ln)

        print("\n" + "=" * 60)
        print("Workflow 完成：3 个 Agent 已通过共享状态完成信息互通。")
        print("=" * 60)
        return self.state
