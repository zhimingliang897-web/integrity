@echo off
echo [System] 使用 cli.py 一键处理 3D 课程...

call "E:\anaconda_laptop\Scripts\activate.bat" coursedigest
cd /d E:\integrity\13course_digest

python cli.py all cache/3d

pause