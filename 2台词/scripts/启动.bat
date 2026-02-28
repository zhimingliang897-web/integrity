@echo off
cd /d "%~dp0.."
setlocal
where python >nul 2>&1
if errorlevel 1 (
  where py >nul 2>&1
  if errorlevel 1 (
    where docker >nul 2>&1
    if not errorlevel 1 (
      pushd docker
      docker compose up -d
      popd
      start "" "http://localhost:5000"
      pause
      exit /b 0
    ) else (
      echo 未检测到 Python 或 Docker，需安装 Python 3.11+ 或 Docker Desktop
      pause
      exit /b 1
    )
  ) else (
    set "PY_BOOT=py -3"
  )
) else (
  set "PY_BOOT=python"
)
if not exist ".venv\Scripts\python.exe" (
  %PY_BOOT% -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -c "import flask,requests,pdfplumber,edge_tts" >nul 2>&1
if errorlevel 1 (
  python -m pip install --no-cache-dir flask requests pdfplumber edge-tts
)
start "" /b python app.py
powershell -Command "$ErrorActionPreference='SilentlyContinue'; for($i=0;$i -lt 30;$i++){try{ $r=Invoke-WebRequest -UseBasicParsing http://localhost:5000/; if($r.StatusCode -eq 200){exit 0} }catch{} Start-Sleep -Seconds 1 }; exit 1"
start "" "http://localhost:5000"
pause
endlocal
