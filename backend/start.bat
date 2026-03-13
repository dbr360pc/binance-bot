@echo off
cd /d "%~dp0"
echo.
echo  To create or reset the admin user, run:
echo    .venv\Scripts\python create_admin.py
echo.
echo Starting FastAPI backend...
"%~dp0.venv\Scripts\uvicorn.exe" app.main:app --reload --host 0.0.0.0 --port 8000
pause
