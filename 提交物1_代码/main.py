# main.py
import os
from dotenv import load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
# ========== 这里换成 ConversationBufferMemory ==========
from langchain.memory import ConversationBufferMemory
from tools import code_static_analysis

# 加载.env密钥
load_dotenv()

# 初始化通义千问 qwen-plus
llm = ChatTongyi(
    model="qwen-plus",
    dashscope_api_key=os.environ.get("DASHSCOPE_API_KEY"),
    temperature=0.3
)

# 注册工具
tools = [code_static_analysis]

# 上下文记忆（替换为 ConversationBufferMemory，用法完全一样）
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ReAct提示词
react_prompt = PromptTemplate.from_template("""
你是专业Python代码审查助手。
用户提交代码时，优先调用code_static_analysis工具拿到静态分析结果，结合工具输出做代码审查。
输出内容需要包含：潜在Bug风险、代码坏味道、改进建议。

可用工具：{tools}
工具名称列表：{tool_names}

历史对话记录：
{chat_history}

用户输入：{input}
{agent_scratchpad}
""")

# 创建Agent
agent = create_react_agent(llm, tools, react_prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5
)

def cli_interactive():
    print("=====代码审查Agent Homework1（通义千问）=====")
    print("使用方式：")
    print("  1. 直接粘贴代码，最后一行输入END提交")
    print("  2. 输入 file:文件路径 （例如 file:examples/test_code.py）直接读取文件审查")
    print("输入 exit 退出程序\n")
    while True:
        print("----- 请输入要求（最后一行输入END提交）-----")
        code_lines = []
        while True:
            line = input()
            # 输入exit直接退出
            if line.strip().lower() == "exit":
                print("程序结束")
                return
            # 输入END结束本次输入
            if line.strip() == "END":
                break
            code_lines.append(line)
        
        user_input = "\n".join(code_lines).strip()
        
        # 判断是不是文件读取模式
        if user_input.startswith("file:"):
            file_path = user_input[5:].strip()
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    user_input = f.read()
                print(f"✅ 已读取文件：{file_path}")
            except Exception as e:
                print(f"❌ 读取文件失败：{e}")
                continue
        
        try:
            result = agent_executor.invoke({"input": user_input})
            print("\n========审查报告输出========\n")
            print(result["output"])
            print("\n-----------------------------\n")
        except Exception as err:
            print(f"\n[系统出错] {err}，请重新输入\n")




if __name__ == "__main__":
    cli_interactive()
