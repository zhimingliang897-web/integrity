@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================
echo     Cookie 自动获取工具
echo ======================================
echo.
echo 请选择要获取Cookie的平台:
echo   1) 抖音 (douyin)
echo   2) 小红书 (xiaohongshu)
echo   3) B站 (bilibili)
echo   4) 全部平台
echo.
set /p choice=请输入选项 (1/2/3/4):

if "%choice%"=="1" goto douyin
if "%choice%"=="2" goto xiaohongshu
if "%choice%"=="3" goto bilibili
if "%choice%"=="4" goto all

echo 无效的选项
pause
exit /b 1

:douyin
echo.
echo 正在获取抖音Cookie...
python scripts\refresh_cookie.py -p douyin
goto end

:xiaohongshu
echo.
echo 正在获取小红书Cookie...
python scripts\refresh_cookie.py -p xiaohongshu
goto end

:bilibili
echo.
echo 正在获取B站Cookie...
python scripts\refresh_cookie.py -p bilibili
goto end

:all
echo.
echo === 获取抖音Cookie ===
python scripts\refresh_cookie.py -p douyin
echo.
echo === 获取小红书Cookie ===
python scripts\refresh_cookie.py -p xiaohongshu
echo.
echo === 获取B站Cookie ===
python scripts\refresh_cookie.py -p bilibili
goto end

:end
echo.
echo ======================================
echo Cookie获取完成!
echo 配置文件已自动更新
echo ======================================
pause
