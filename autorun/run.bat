@echo off
chcp 65001 >nul
echo ========================================
echo Orchestrator + Cursor Worker 工作流
echo ========================================
echo.

cd /d %~dp0

echo 检查 Python 环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo.
echo 启动 Orchestrator...
echo.

python orchestrator.py

pause

