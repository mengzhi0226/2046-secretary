@echo off
chcp 65001 >nul
cd /d "c:\Users\hrgap\OneDrive\Desktop\2046孟之CC"
echo [%date% %time%] jiankangz starting...
powershell -ExecutionPolicy Bypass -File scripts\agent_jiankangz.ps1
echo [%date% %time%] jiankangz done.
