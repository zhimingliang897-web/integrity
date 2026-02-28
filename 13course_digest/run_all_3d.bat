@echo off
setlocal enabledelayedexpansion

echo [System] 正在使用智能路径模式处理 3D 课程...
echo (注意：请确保文件位于 input/ 目录及其子目录下)

:: 定义公共课件和真题（只需写文件名）
set "COMMON_PPT=extracted_pages.pdf"
set "COMMON_EXAMS=AI6131-Quiz.pdf"

:: 循环处理 1-5 课
for /L %%i in (1,1,5) do (
    echo.
    echo ------------------------------------------
    echo [Step %%i/5] 正在分析: 3d%%i.mp4
    
    :: 自动判断该课程是否有专属论文 (1.pdf, 2.pdf, 3.pdf)
    set "PAPER_ARG="
    if exist "input/3d_course/%%i.pdf" (
        set "PAPER_ARG=--paper %%i.pdf"
    ) else if exist "cache/3d/%%i.pdf" (
        set "PAPER_ARG=--paper %%i.pdf"
    )
    
    python main.py "3d%%i.mp4" --ppt "%COMMON_PPT%" --exams "%COMMON_EXAMS%" !PAPER_ARG!
    
    if errorlevel 1 (
        echo [Error] 处理 3d%%i 失败。
        pause
    )
)

echo.
echo ✅ 全部处理任务提交完毕！
pause
