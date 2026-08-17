@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [UOSSM Audit] Creating local Python environment...
    py -m venv .venv
    if errorlevel 1 goto :error
)

echo [UOSSM Audit] Checking dependencies...
".venv\Scripts\python.exe" -c "import streamlit,pandas,openpyxl,xlrd" >nul 2>&1
if errorlevel 1 (
    echo [UOSSM Audit] Installing required packages...
    ".venv\Scripts\python.exe" -m pip install -r requirements-local.txt
    if errorlevel 1 goto :error
)

echo [UOSSM Audit] Starting at http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run app_quality12.py
goto :end

:error
echo.
echo Failed to prepare or start the application.
pause

:end
endlocal
