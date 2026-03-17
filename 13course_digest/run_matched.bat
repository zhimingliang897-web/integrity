@echo off
echo 开始执行 AI 自动匹配生成的任务组合...

echo ===============================
echo 正在处理 AI 匹配的视频: 7.mp4...
python main.py "E:\integrity\13course_digest\cache\time\7.mp4"
if errorlevel 1 goto end

echo ===============================
echo 正在处理 AI 匹配的视频: 5.mp4...
python main.py "E:\integrity\13course_digest\cache\time\5.mp4" --ppt "E:\integrity\13course_digest\cache\time\Midterm Review.pdf"
if errorlevel 1 goto end

echo ===============================
echo 正在处理 AI 匹配的视频: 2.mp4...
python main.py "E:\integrity\13course_digest\cache\time\2.mp4" --ppt "E:\integrity\13course_digest\cache\time\0. Introduction.pdf"
if errorlevel 1 goto end

echo ===============================
echo 正在处理 AI 匹配的视频: 8.mp4...
python main.py "E:\integrity\13course_digest\cache\time\8.mp4"
if errorlevel 1 goto end

echo ===============================
echo 正在处理 AI 匹配的视频: 1.mp4...
python main.py "E:\integrity\13course_digest\cache\time\1.mp4"
if errorlevel 1 goto end

echo ===============================
echo 正在处理 AI 匹配的视频: 6.mp4...
python main.py "E:\integrity\13course_digest\cache\time\6.mp4" --ppt "E:\integrity\13course_digest\cache\time\0. Introduction.pdf"
if errorlevel 1 goto end

echo ===============================
echo 正在处理 AI 匹配的视频: 3.mp4...
python main.py "E:\integrity\13course_digest\cache\time\3.mp4" --ppt "E:\integrity\13course_digest\cache\time\1. Characteristics of Time Series.pdf"
if errorlevel 1 goto end

echo ===============================
echo 正在处理 AI 匹配的视频: 4.mp4...
python main.py "E:\integrity\13course_digest\cache\time\4.mp4"
if errorlevel 1 goto end

:end
echo 所有匹配任务执行完毕。
