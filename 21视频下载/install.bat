@echo off
:: 21视频下载器 - 一键安装 Native Host
:: 运行此脚本即可让浏览器插件直接触发本地下载，无需任何服务器

setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║     21视频下载器 - Native Host 安装      ║
echo  ╚══════════════════════════════════════════╝
echo.

:: ── 获取当前目录（脚本所在目录）
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "HOST_PY=%ROOT%\native_host.py"
set "MANIFEST_PATH=%ROOT%\com.videodl.native.json"

echo [1/4] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ 未找到 Python，请先安装 Python 3.8+
    pause & exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  ✅ %PYVER%

echo.
echo [2/4] 检查 yt-dlp...
yt-dlp --version >nul 2>&1
if errorlevel 1 (
    echo  ⚙️  正在安装 yt-dlp...
    pip install yt-dlp -q
) else (
    for /f "tokens=*" %%i in ('yt-dlp --version 2^>^&1') do set YTVER=%%i
    echo  ✅ yt-dlp !YTVER!
)

echo.
echo [3/4] 生成 Native Messaging 配置文件...

:: 获取 python 的完整路径
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%i

:: 把反斜杠转义成 JSON 友好的格式
set "PYTHON_JSON=!PYTHON_EXE:\=\\!"
set "SCRIPT_JSON=!HOST_PY:\=\\!"

:: 生成 manifest JSON
(
echo {
echo   "name": "com.videodl.native",
echo   "description": "21视频下载器 Native Host",
echo   "path": "!PYTHON_JSON!",
echo   "type": "stdio",
echo   "allowed_origins": [
echo     "chrome-extension://*/",
echo     "edge-extension://*/"
echo   ],
echo   "args": ["!SCRIPT_JSON!"]
echo }
) > "%MANIFEST_PATH%"

echo  ✅ 配置文件已生成: %MANIFEST_PATH%

echo.
echo [4/4] 注册到 Windows 注册表...

:: Chrome
reg add "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.videodl.native" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f >nul 2>&1
if not errorlevel 1 echo  ✅ Chrome 注册成功

:: Edge
reg add "HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.videodl.native" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f >nul 2>&1
if not errorlevel 1 echo  ✅ Edge 注册成功

:: Chrome Canary
reg add "HKCU\Software\Google\Chrome Canary\NativeMessagingHosts\com.videodl.native" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f >nul 2>&1

echo.
echo  ══════════════════════════════════════════
echo  🎉 安装完成！
echo.
echo  接下来:
echo  1. 打开 Chrome/Edge，进入 chrome://extensions/
echo  2. 开启"开发者模式"
echo  3. 点击"加载已解压的扩展程序"
echo  4. 选择: %ROOT%\extension 文件夹
echo  5. 安装完成后，在任意网页播放视频后点击插件即可下载！
echo.
echo  下载文件保存在: %ROOT%\downloads\
echo  ══════════════════════════════════════════
echo.
pause
