@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo 正在运行 Homework2 Workflow MVP 自动化可行性测试...
echo.
python test_workflow.py
if errorlevel 1 (
    echo.
    echo [提示] 若提示 python 不是命令，请改用 py test_workflow.py 或安装 Python 并加入 PATH。
    pause
    exit /b 1
)
echo.
echo 测试完成，按任意键关闭窗口。
pause
