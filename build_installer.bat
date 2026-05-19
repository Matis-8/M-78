@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo M-78 PROFESSIONAL INSTALLER BUILDER
echo ==================================================

:: STEP 1: Build PyInstaller executable (Folder mode for Inno Setup)
echo [STEP 1/3] Running PyInstaller...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

.venv\Scripts\python -m PyInstaller --noconsole ^
    --icon="assets/icons/m78_icon.ico" ^
    --name="M-78" ^
    --add-data ".venv\Lib\site-packages\faster_whisper\assets;faster_whisper/assets" ^
    --add-data "assets/models/whisper-base;assets/models/whisper-base" ^
    --add-data "app/dashboard;app/dashboard" ^
    --add-data "assets/icons/m78_icon.ico;assets/icons" ^
    --hidden-import="webview" ^
    --hidden-import="fastapi" ^
    --hidden-import="uvicorn" ^
    --hidden-import="psutil" ^
    --hidden-import="keyboard" ^
    --hidden-import="win32gui" ^
    --hidden-import="win32con" ^
    launcher.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed. Ensure .venv is ready.
    pause
    exit /b
)

:: STEP 2: Compile .iss using Inno Setup
echo [STEP 2/3] Compiling Setup Script (ISCC)...

set "ISCC=iscc.exe"
where "%ISCC%" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    set "ISCC=C:\Users\Administrator\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
    if not exist "!ISCC!" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not exist "!ISCC!" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if exist "!ISCC!" (
    "!ISCC!" setup.iss
) else (
    echo [WARNING] Inno Setup (ISCC.exe) not found on this machine.
    echo Please install Inno Setup from: https://jrsoftware.org/isdl.php
    echo Then run this script again or compile 'setup.iss' manually.
    pause
    exit /b
)

:: STEP 3: Generate final M-78 Setup.exe
echo [STEP 3/3] Finalizing Release...
if exist "dist-installer\M-78-Setup.exe" (
    echo [SUCCESS] Final Installer Generated: dist-installer\M-78-Setup.exe
) else (
    echo [ERROR] Installer generation failed. Check setup.iss.
)

echo ==================================================
echo BUILD PROCESS COMPLETE
echo ==================================================
pause
