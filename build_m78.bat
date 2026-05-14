@echo off
echo [M-78] Building Premium Desktop Executable...

:: Ensure we are in the project root
cd /d "%~dp0"

:: PyInstaller Command with Branding Keys
:: --noconsole: Hide the terminal window
:: --icon: Apply the custom M-78 identity to the .exe file
:: --add-data: Include frontend and assets
:: --name: Official application name

.venv\Scripts\python -m PyInstaller --noconsole ^
    --icon="assets/icons/m78_icon.ico" ^
    --name="M-78" ^
    --add-data "app/dashboard;app/dashboard" ^
    --add-data "assets/icons/m78_icon.ico;assets/icons" ^
    --hidden-import="pywebview" ^
    --hidden-import="fastapi" ^
    --hidden-import="uvicorn" ^
    --hidden-import="psutil" ^
    --hidden-import="keyboard" ^
    launcher.py

echo [M-78] Build complete. Check the 'dist' folder.
pause
