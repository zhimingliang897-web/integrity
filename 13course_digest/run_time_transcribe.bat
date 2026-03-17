@echo off
echo ========================================
echo 课程 Time Series Analysis 转录脚本
echo ========================================
echo.
echo 当前已转录: 1.mp4, 2.mp4
echo 待转录: 3.mp4 - 8.mp4 (共6个视频，约18小时)
echo.
echo 使用 conda coursedigest 环境运行...
echo.
echo 开始转录剩余视频...
conda run -n coursedigest python cli.py all cache/time
echo.
echo 转录完成！
pause