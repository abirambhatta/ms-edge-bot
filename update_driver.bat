@echo off
pushd "%~dp0"
echo Matching msedgedriver.exe to the installed Edge...

if not exist .venv (
    echo Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python ms-edge-bot-main\edge.py --update-driver
pause
