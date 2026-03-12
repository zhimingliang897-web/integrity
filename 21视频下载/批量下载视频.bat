@echo off
chcp 65001 >nul
title 批量下载视频（智能版）

echo.
echo ========================================
echo   批量视频下载器 - 智能版
echo ========================================
echo.
echo   适用场景：一个课程页面有多个视频
echo   功能：自动扫描、批量收集、并发下载
echo.

python "%~dp0batch_downloader.py"

pause
