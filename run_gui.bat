@echo off
pushd "%~dp0"
echo ============================================================
echo Microsoft Edge Search Bot - GUI
echo ============================================================
echo.

if not exist .venv (
    echo Error: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Starting GUI...
echo.
python ms-edge-bot-main\gui.py

if %errorlevel% neq 0 (
    echo.
    echo Error: GUI failed to start
    echo Check the error message above
    pause
)
