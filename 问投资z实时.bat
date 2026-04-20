@echo off
chcp 65001 >nul
cd /d "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
if "%1"=="" (
    powershell -ExecutionPolicy Bypass -File scripts\ask_touzi_realtime.ps1
) else (
    powershell -ExecutionPolicy Bypass -File scripts\ask_touzi_realtime.ps1 %1
)
