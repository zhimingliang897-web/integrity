@echo off
REM 一键运行：GTX 1060 + coursedigest 环境 + 6103 整门课

call "E:\anaconda_laptop\Scripts\activate.bat" coursedigest
cd /d E:\integrity\13course_digest

python dl_generate.py cache/dl/6103 --transcribe-all

pause

