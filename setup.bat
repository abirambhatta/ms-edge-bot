@echo off
echo ============================================================
echo Microsoft Edge Search Bot - Setup Script
echo ============================================================
echo.

echo [1/3] Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)
echo Done!
echo.

echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat
echo Done!
echo.

echo [3/3] Installing dependencies...
pip install -r ms-edge-bot-main\requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo Done!
echo.

echo ============================================================
echo Setup completed successfully!
echo ============================================================
echo.
echo Next steps:
echo 1. Activate virtual environment: .venv\Scripts\activate
echo 2. Run the GUI: run_gui.bat
echo 3. Or check your profile: python ms-edge-bot-main\check_profile.py
echo.
echo The bot will automatically fetch 100 keywords from Wikipedia!
echo - PC searches: 34 random keywords
echo - Mobile searches: 24 random keywords
echo - Keywords auto-update every 18 hours
echo.
pause
