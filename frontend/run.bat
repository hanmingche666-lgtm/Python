@echo off
chcp 65001 >nul
title 体质健康分类 - 前端 (port 5173)

cd /d "%~dp0"

:: 检查 Node.js
node --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请安装 Node.js 并确保已添加到系统 PATH
    echo        下载地址: https://nodejs.org/
    pause
    exit /b 1
)
echo [信息] Node.js 版本:
node --version

:: 检查 npm
npm --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] npm 未找到
    pause
    exit /b 1
)

:: 安装依赖
if not exist "node_modules\" (
    echo [1/2] 正在安装前端依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [1/2] node_modules 已存在，跳过安装
)

:: 启动
echo [2/2] 启动 Vite 开发服务器...
echo.
echo    前端地址: http://127.0.0.1:5173
echo    确保后端已启动 (http://127.0.0.1:8000)
echo    按 Ctrl+C 停止服务
echo.
call npx vite --host

pause
