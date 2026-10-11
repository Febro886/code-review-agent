# tools.py
import ast
from langchain.tools import tool

@tool
def code_static_analysis(code: str) -> str:
    """
    【工具】对输入Python代码做静态AST解析，**不会运行代码**；提取函数名、变量，捕获语法错误。
    参数 code：待审查的Python源代码字符串
    返回：解析得到的代码结构信息
    """
    try:
        tree = ast.parse(code)
        func_list = []
        assign_vars = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_list.append(node.name)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if hasattr(target, "id"):
                        assign_vars.append(target.id)
        info = f"""
===静态解析结果===
检测到函数：{func_list}
顶层赋值变量：{assign_vars}
语法校验：代码语法合法无解析错误
"""
        return info
    except SyntaxError as e:
        return f"【语法错误】解析失败：行{e.lineno}, 错误信息:{e.msg}"
