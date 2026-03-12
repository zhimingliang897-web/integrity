@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 正在检查嗅探器需要的依赖...
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo 首次使用，正在为您安装 Playwright (可能需要1-2分钟下载浏览器内核)...
    pip install playwright -q
    playwright install chromium
    echo 依赖安装完成！
)

python sniffer.py
pause
