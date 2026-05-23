@echo off
echo ============================================================
echo Microsoft Edge Profile Checker
echo ============================================================
echo.

if not exist .venv (
    echo Error: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Starting profile checker...
echo.
python ms-edge-bot-main\check_profile.py

pause
