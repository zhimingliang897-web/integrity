@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

cd /d "%~dp0"

color 0A
title 分镜视频生成器 - 启动中...
cls

echo.
echo ========================================
echo   分镜视频生成器一键启动
echo ========================================
echo.

REM ============ 1. 检查 Python ============
echo [步骤 1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未找到 Python！
    echo 请下载安装: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PY_VERSION=%%i
echo [成功] %PY_VERSION%
echo.

REM ============ 2. 检查并安装依赖 ============
echo [步骤 2/3] 检查依赖包...
python -c "import PIL; import edge_tts; import openai" >nul 2>&1

if errorlevel 1 (
    echo [提示] 部分依赖缺失，正在安装...
    echo 可能需要1-2分钟，请耐心等待...
    echo.
    python -m pip install -q pillow edge-tts openai
    
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败！
        echo 请手动执行以下命令:
        echo   python -m pip install pillow edge-tts openai
        echo.
        pause
        exit /b 1
    )
)
echo [成功] 所有依赖已就绪
echo.

REM ============ 3. 启动应用 ============
echo [步骤 3/3] 启动分镜视频生成器...
title 分镜视频生成器
echo.

python app.py
if errorlevel 1 (
    echo.
    echo [错误] 应用启动失败！
    echo.
    pause
    exit /b 1
)

endlocal
