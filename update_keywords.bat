@echo off
echo ============================================================
echo Update Search Keywords from Wikipedia
echo ============================================================
echo.

if not exist .venv (
    echo Error: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Fetching fresh keywords from Wikipedia...
echo.
python ms-edge-bot-main\keyword_fetcher.py

pause
