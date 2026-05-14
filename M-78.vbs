Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where the .vbs script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

' Determine the Python executable path
' Priority: 1. .venv (local), 2. venv (local), 3. system pythonw
pythonExe = scriptDir & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(pythonExe) Then
    pythonExe = scriptDir & "\venv\Scripts\pythonw.exe"
End If
If Not fso.FileExists(pythonExe) Then
    pythonExe = "pythonw.exe"
End If

' Run the launcher silently
WshShell.Run chr(34) & pythonExe & Chr(34) & " launcher.py", 0
Set WshShell = Nothing
Set fso = Nothing
