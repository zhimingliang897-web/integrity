@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title 文件助手 Agent
color 0A
echo.
echo  ================================================
echo    文件助手 Agent - 启动中...
echo  ================================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM Install dependencies
echo  [1/3] 检查并安装依赖...
pip install -q flask openai python-docx PyPDF2
echo  依赖检查完成
echo.

REM Check for tunnel tools (natapp first, then cloudflared)
set TUNNEL_STARTED=0

REM natapp (国内推荐)
if exist "natapp.exe" (
    echo  [2/3] 启动 natapp 内网穿透...
    for /f "delims=" %%i in ('python -c "import json, sys; sys.stdout.write(json.load(open('config.json', encoding='utf-8')).get('natapp_token', ''))" 2^>nul') do set NAT_TOKEN=%%i
    if not "!NAT_TOKEN!"=="" (
        start "natapp - 公网链接在这里" cmd /k "natapp.exe -authtoken=!NAT_TOKEN!"
    ) else (
        start "natapp - 公网链接在这里" cmd /k "natapp.exe -authtoken=2f2ad52617d62251"
    )
    set TUNNEL_STARTED=1
    echo  公网链接在刚弹出的 [natapp] 窗口里查看（等几秒出现 Forwarding 那行）
    echo.
    goto START_FLASK
)

REM cloudflared amd64
if exist "cloudflared-windows-amd64.exe" (
    echo  [2/3] 启动 Cloudflare Tunnel...
    start "Cloudflare Tunnel - 公网链接在这里" cmd /k "cloudflared-windows-amd64.exe tunnel --url http://localhost:5000"
    set TUNNEL_STARTED=1
    echo  公网链接在刚弹出的 [Cloudflare Tunnel] 窗口里查看
    echo.
    goto START_FLASK
)

REM cloudflared generic
if exist "cloudflared.exe" (
    echo  [2/3] 启动 Cloudflare Tunnel...
    start "Cloudflare Tunnel - 公网链接在这里" cmd /k "cloudflared.exe tunnel --url http://localhost:5000"
    set TUNNEL_STARTED=1
    echo  公网链接在刚弹出的 [Cloudflare Tunnel] 窗口里查看
    echo.
    goto START_FLASK
)

echo  [2/3] 未找到隧道工具，仅局域网可访问
echo       推荐使用 natapp.cn（免费）获取外网链接
echo.

:START_FLASK
echo  [3/3] 启动 Web 服务...
echo.
echo  本机访问：   http://localhost:5000
echo  局域网访问： http://192.168.0.242:5000
echo.
echo  按 Ctrl+C 停止服务
echo  ================================================
echo.
python app.py
pause
