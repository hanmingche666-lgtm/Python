@echo off
chcp 65001 >nul
title 体质健康分类 - 后端 API (port 8000)

cd /d "%~dp0"

:: 检查 Python
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请安装 Python 3.9+ 并确保已添加到 PATH
    echo        下载: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [信息] Python 版本:
python --version

:: 安装依赖
echo.
echo [1/2] 检查依赖...
pip install -r requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo [警告] 依赖安装有问题，继续尝试...
)

:: 启动
echo.
echo [2/2] 启动 FastAPI 服务...
echo.
echo    后端地址: http://127.0.0.1:8000
echo    API 文档: http://127.0.0.1:8000/docs
echo    按 Ctrl+C 停止服务
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
