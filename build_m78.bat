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
    --icon="m78_icon.ico" ^
    --name="M-78" ^
    --add-data "frontend;frontend" ^
    --add-data "m78_icon.ico;." ^
    --hidden-import="pywebview" ^
    --hidden-import="fastapi" ^
    --hidden-import="uvicorn" ^
    launcher.py

echo [M-78] Build complete. Check the 'dist' folder.
pause
