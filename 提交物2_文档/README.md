```
Homework 1 代码审查Agent
学号：2412190206 姓名：宋泽轶
作业方向：代码审查Agent
项目目标：搭建代码助手Agent，练习LLM调用、Prompt设计、工具集成。
实现标准Agent循环：输入 → 推理 → 工具调用 → 输出。

## 功能
1. 接收用户输入Python代码
2. 调用AST静态解析工具，分析代码结构
3. 大模型结合工具结果，发现潜在Bug，给出改进建议
4. 支持多轮对话上下文记忆
5. 命令行交互，具备异常容错处理

## 技术栈
- Python 3.11
- LangChain ReAct Agent框架
- LLM：通义千问 qwen-plus
- 自定义工具：code_static_analysis（AST静态代码解析）

## 部署运行
1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

2. 安装依赖
pip install -r requirements.txt

3. 在项目根目录新建.env文件，填入通义千问API密钥
DASHSCOPE_API_KEY="你的密钥"

4. 启动程序
python main.py

粘贴代码，全部输入完成后新起一行输入END回车提交；输入exit退出。

## 测试样例
测试输入代码：
def calc(a,b):
    return a / b
data = [1,2,3]
print(data[10])

Agent识别除零风险、列表索引越界，输出修复建议。

```