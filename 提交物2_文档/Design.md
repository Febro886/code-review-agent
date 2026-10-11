```
Design.md 设计文档
学号：2412190206 姓名：宋泽轶

## 整体架构
本项目基于LangChain ReAct模式实现完整Agent循环流程：
用户输入代码 → 组装Prompt并带上历史记忆 → LLM推理思考
→ 判断是否调用工具 → 调用自定义静态代码分析工具
→ 获取工具返回结果送入大模型
→ 整理最终审查结果输出

### 文件分工
1. main.py
    - Agent、大模型初始化
    - ConversationBufferMemory上下文记忆管理
    - AgentExecutor执行调度
    - 命令行多行交互逻辑、全局异常捕获
2. tools.py
    - 自定义工具 code_static_analysis
    - 使用Python ast模块解析抽象语法树，提取函数、变量，捕获语法错误
3. .env：保存API密钥，提交作业不包含该文件

## 核心组件
1. ConversationBufferMemory：保存对话历史，支持多轮追问
2. ReAct Agent：负责思考-行动循环，决定什么时候调用工具
3. AgentExecutor：调度大模型与工具，设置max_iterations=5，防止无限循环
4. code_static_analysis工具：仅静态解析代码，不会执行用户代码，保证安全

## 错误处理策略
1. handle_parsing_errors：处理大模型输出格式解析异常，程序不崩溃
2. 工具内部捕获SyntaxError语法错误，把错误信息返回大模型
3. 最外层try-except捕获运行时异常，打印提示回到交互界面
4. 限制最大迭代次数，避免Agent死循环

## 边界情况处理
1. 输入非Python代码：工具解析报错，大模型提示输入合法Python代码
2. 代码存在语法错误：工具捕获行号、错误信息，写进审查报告
3. 多轮对话：记忆保存历史，可以继续追问优化方案

## 扩展方向
1. 新增读取本地py文件的工具
2. 增加Web网页界面替代命令行
```