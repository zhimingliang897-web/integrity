@echo off
chcp 65001
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo Starting Social Media Analysis GUI...
python -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] streamlit is not installed.
  echo Please run: pip install -r requirements.txt
  pause
  exit /b 1
)

python -m streamlit run gui.py
pause
