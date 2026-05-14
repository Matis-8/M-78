; M-78 Inno Setup Script
; -----------------------
; To build the installer: 
; 1. Generate the distribution folder with PyInstaller: .venv\Scripts\python -m PyInstaller --noconsole --name="M-78" launcher.py
; 2. Run this script in Inno Setup (ISCC.exe)

[Setup]
AppId={{D3E8C1A2-F2B3-4A5D-B6C7-E8F9A0B1C2D3}}
AppName=M-78 Premium Dictation
AppVersion=1.0.0
AppPublisher=Matis-8
DefaultDirName={autopf}\M-78
DefaultGroupName=M-78
OutputDir=dist-installer
OutputBaseFilename=M-78-Setup
SetupIconFile=assets\icons\m78_icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\M-78.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\M-78\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: The database is auto-created on first run, so no need to bundle a blank one.

[Icons]
Name: "{group}\M-78"; Filename: "{app}\M-78.exe"
Name: "{autodesktop}\M-78"; Filename: "{app}\M-78.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\M-78.exe"; Description: "{cm:LaunchProgram,M-78}"; Flags: nowait postinstall skipifsilent
