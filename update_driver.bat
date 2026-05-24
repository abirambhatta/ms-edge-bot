@echo off
echo ============================================================
echo Edge Driver Auto-Updater
echo ============================================================
echo.

if not exist .venv (
    echo Error: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Installing webdriver-manager...
pip install webdriver-manager --upgrade

echo.
echo Downloading latest Edge driver...
python -c "from webdriver_manager.microsoft import EdgeChromiumDriverManager; print(EdgeChromiumDriverManager().install())"

echo.
echo ============================================================
echo Driver updated! Copy the path shown above and update your
echo msedgedriver.exe location, or just use webdriver-manager
echo in the code.
echo ============================================================
pause
