import os
import urllib.request

from llm import LLMClient
from state import SharedState
from agents import RequirementAgent, DesignAgent, CodingAgent
from workflow import Workflow


def _load_env_file():
    """简易读取项目根目录 .env（避免引入 python-dotenv 依赖）。

    把 Key 放入 .env 后，运行本脚本无需每次手动 set 环境变量。"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


_load_env_file()

# 三个不同的免费模型（均经实测免费可用，国内可访问、OpenAI 兼容）。
# 注：原计划的 DeepSeek 官方（deepseek-chat / reasoner）对该 Key 返回 402 需付费，
# 故弃用，改为「智谱 AI 两个不同免费模型 + 阿里百炼一个免费模型」，保证三个 Agent 都用免费模型。
# 若某 Key 未配置，对应 Agent 自动降级为 mock 模板，流程仍能跑通。
PLATFORMS = [
    {
        "role": "需求Agent",
        "label": "智谱 AI（glm-4-air）",
        "model": "glm-4-air",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "key_env": "ZHIPU_API_KEY",
    },
    {
        "role": "设计Agent",
        "label": "智谱 AI（glm-4-flash）",
        "model": "glm-4-flash",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "key_env": "ZHIPU_API_KEY",
    },
    {
        "role": "编码Agent",
        "label": "智谱 AI（glm-3-turbo）",
        "model": "glm-3-turbo",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "key_env": "ZHIPU_API_KEY",
    },
]


def build_agents():
    """三个 Agent 分别接入三个不同的国内免费平台（每个平台一个免费模型）。"""
    llms = {}
    for p in PLATFORMS:
        key = os.getenv(p["key_env"])
        if key:
            llm = LLMClient(
                provider="openai",
                model=p["model"],
                api_key=key,
                base_url=p["base_url"],
                label=f"{p['label']} / {p['model']}",
            )
        else:
            llm = LLMClient(
                provider="mock",
                label=f"{p['label']} / {p['model']}（未配置 Key，降级 mock）",
            )
        llms[p["role"]] = llm

    return [
        RequirementAgent(llms["需求Agent"]),
        DesignAgent(llms["设计Agent"]),
        CodingAgent(llms["编码Agent"]),
    ]


def main():
    print("=" * 60)
    print("环境检测（3 个 Agent 的真实引擎）：")
    for p in PLATFORMS:
        key = os.getenv(p["key_env"])
        if key:
            print(f"  {p['label']} ({p['key_env']}): 已设置 -> 将使用真实模型 {p['model']}")
        else:
            print(f"  {p['label']} ({p['key_env']}): 未设置 -> 该 Agent 自动降级 mock 模板")
    print("=" * 60)

    print("请描述你的产品需求（例如：我想做一个待办事项系统，支持创建任务、设置截止日期、标记完成。）")
    requirement = input("需求描述（回车使用默认示例）：").strip()
    if not requirement:
        requirement = (
            "我想做一个帮助团队管理任务的待办事项系统，"
            "支持创建任务、设置截止日期、标记完成，并支持多人协作。"
        )

    state = SharedState()
    agents = build_agents()
    wf = Workflow(agents, state)
    wf.run(requirement)

    # 本次运行不落盘保存，三个 Agent 的完整产出已在上方终端直接输出
    print("\n流程结束：需求Agent -> 设计Agent -> 编码Agent 已通过共享状态完成信息互通。")


if __name__ == "__main__":
    main()
