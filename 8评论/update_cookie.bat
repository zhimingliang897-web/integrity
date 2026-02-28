@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================
echo Cookie Refresh Tool
echo ======================================
echo 1) douyin
echo 2) xiaohongshu
echo 3) bilibili
echo.
set /p choice=Select platform (1/2/3): 

if "%choice%"=="1" set platform=douyin
if "%choice%"=="2" set platform=xiaohongshu
if "%choice%"=="3" set platform=bilibili

if "%platform%"=="" (
  echo Invalid selection.
  pause
  exit /b 1
)

echo.
echo Running: python scripts\refresh_cookie.py -p %platform%
python scripts\refresh_cookie.py -p %platform%
echo.
pause
