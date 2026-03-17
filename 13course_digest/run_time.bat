@echo off
echo [System] 启动 time 课程全流程处理...

call "E:\anaconda_laptop\Scripts\activate.bat" coursedigest
cd /d E:\integrity\13course_digest

python cli.py all cache/time

echo.
echo 处理完成！请检查 output/ 目录。
pause