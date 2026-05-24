@echo off
echo ============================================================
echo Microsoft Edge Search Automator - Setup
echo ============================================================
echo.

REM ── Step 1: Check for Python ─────────────────────────────────
echo [1/4] Checking for Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Found: %%v
    goto :venv
)

echo Python is not installed on this system.
echo.

REM ── Try installing via winget (Windows 10/11 built-in) ───────
echo Trying to install Python automatically via Windows Package Manager...
winget --version >nul 2>&1
if %errorlevel% neq 0 goto :manual_install

echo Running: winget install Python 3.11 ...
echo This may take a few minutes. Please wait.
echo.
winget install --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 goto :manual_install

echo.
echo Python installed! Restarting setup with updated PATH...
echo.
start "" cmd /c ""%~f0""
exit /b 0

:manual_install
echo.
echo ============================================================
echo  Could not install Python automatically.
echo.
echo  Please install it manually:
echo    1. Go to: https://www.python.org/downloads/
echo    2. Download the latest Python 3.x installer
echo    3. Run the installer and CHECK "Add Python to PATH"
echo    4. Re-run this setup.bat file
echo ============================================================
echo.
pause
exit /b 1

REM ── Step 2: Create virtual environment ───────────────────────
:venv
echo.
echo [2/4] Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)
echo Done!
echo.

REM ── Step 3: Activate venv ────────────────────────────────────
echo [3/4] Activating virtual environment...
call .venv\Scripts\activate.bat
echo Done!
echo.

REM ── Step 4: Install dependencies ─────────────────────────────
echo [4/4] Installing dependencies...
pip install -r ms-edge-bot-main\requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)
echo Done!
echo.

echo ============================================================
echo Setup completed successfully!
echo ============================================================
echo.
echo To launch the application, run:  run_gui.bat
echo.
echo Notes:
echo   - Keywords auto-update every 18 hours from Wikipedia
echo   - Default PC searches: 34 per session
echo   - Default Mobile searches: 24 per session
echo   - You can change these in the Settings tab
echo.
pause
