@echo off
REM SAFE test file with suspicious-looking patterns
echo cmd.exe /c dir
echo powershell.exe -ExecutionPolicy Bypass
echo reg add HKLM\Software\Test
echo schtasks /create /tn TestTask
echo This file is for TESTING ONLY
