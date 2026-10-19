"""Homework2 Workflow MVP —— 自动化可行性测试（零依赖，纯标准库）。

运行：python test_workflow.py
覆盖：
  1) 共享状态通信（Agent 间信息互通）
  2) 三个 Agent 的产出质量（mock 模式）
  3) 端到端流程跑通（输入产品需求描述，含中文/英文/空/特殊字符等边界）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm import LLMClient
from state import SharedState
from agents import RequirementAgent, DesignAgent, CodingAgent
from workflow import Workflow

results = []


def check(name, cond, detail=""):
    results.append(cond)
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}" + (f"  -> {detail}" if detail else ""))


def test_shared_state_communication():
    s = SharedState()
    s.publish("user_requirement", "T", "User")
    check("SharedState: 写入后可读取", s.read("user_requirement") == "T")
    s.publish("req", "R", "需求Agent")
    s.publish("des", "D", "设计Agent")
    # 下游读取上游产物（信息互通核心）
    check("SharedState: 下游读取上游产物", s.read("req") == "R" and s.read("des") == "D")
    check("SharedState: 通信日志完整", len(s.history()) == 3)


def test_agent_outputs():
    req = RequirementAgent(LLMClient(provider="mock"))
    des = DesignAgent(LLMClient(provider="mock"))
    cod = CodingAgent(LLMClient(provider="mock"))
    s = SharedState()
    req_text = "用户想要一个在线订餐平台，支持浏览菜单、下单、查看订单。"
    s.publish("user_requirement", req_text, "User")
    r = req.run(s)   # 需求 Agent 标准化需求文档
    d = des.run(s)   # 设计 Agent 读取需求产物
    c = cod.run(s)   # 编码 Agent 读取设计产物
    check("需求Agent: 产出为结构化需求", ("功能需求" in r) and len(r) > 30)
    # 设计Agent 必须读取到上游需求产物 -> 信息互通（design 引用了需求文档标题）
    check("设计Agent: 读到了需求产物(互通)", "标准化软件需求文档" in d)
    check("编码Agent: 产出含代码骨架", ("class" in c or "def" in c) and len(c) > 50)
    # 编码Agent 必须读取到上游设计产物（引用设计标题 + /tasks 接口）-> 信息互通
    check("编码Agent: 读到了设计产物(互通)", "技术设计文档" in c and "/tasks" in c)


def test_e2e(requirement):
    s = SharedState()
    wf = Workflow(
        [
            RequirementAgent(LLMClient(provider="mock")),
            DesignAgent(LLMClient(provider="mock")),
            CodingAgent(LLMClient(provider="mock")),
        ],
        s,
    )
    try:
        wf.run(requirement)
    except Exception as e:  # noqa: BLE001
        check(f"端到端流程 [{requirement or '<空>'}]: 无异常", False, str(e))
        return
    ok = all(s.read(k) for k in ("requirement", "design", "code"))
    check(f"端到端流程 [{requirement or '<空>'}]: 三产出齐全", ok)


def main():
    print("=" * 60)
    print("Homework2 Workflow MVP —— 自动化可行性测试")
    print("=" * 60)
    test_shared_state_communication()
    test_agent_outputs()
    test_e2e("我想做一个帮助团队管理任务的待办事项系统，支持创建任务、设置截止日期、标记完成。")
    test_e2e("用户想要一个在线订餐平台，支持浏览菜单、下单、查看订单。")
    test_e2e("Build a student grade management system with course and score tracking.")
    test_e2e("")  # 边界：空需求（直接回车）
    test_e2e("Test #1 & 'quote' project description.")  # 边界：特殊字符

    passed = sum(1 for r in results if r)
    total = len(results)
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 通过")
    if passed == total:
        print("结论: 项目可行性验证通过 (可行)")
    else:
        print("结论: 存在失败用例，请检查 (需修复)")
    print("=" * 60)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
