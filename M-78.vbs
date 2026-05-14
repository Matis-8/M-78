Set WshShell = CreateObject("WScript.Shell")
Dim scriptPath
scriptPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptPath
WshShell.Run chr(34) & scriptPath & "\.venv\Scripts\pythonw.exe" & Chr(34) & " launcher.py", 0
Set WshShell = Nothing
