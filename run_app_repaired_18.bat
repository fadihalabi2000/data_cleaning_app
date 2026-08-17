@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -m venv .venv
".venv\Scripts\python.exe" -c "import streamlit,pandas,openpyxl,xlrd,rapidfuzz" >nul 2>&1
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install -r requirements-v2.txt
".venv\Scripts\python.exe" -m streamlit run app_quality18.py
endlocal
