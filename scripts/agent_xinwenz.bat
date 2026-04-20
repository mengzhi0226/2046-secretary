@echo off
chcp 65001 >nul
cd /d "c:\Users\hrgap\OneDrive\Desktop\2046孟之CC"
echo [%date% %time%] xinwenz starting...
powershell -ExecutionPolicy Bypass -File scripts\agent_xinwenz.ps1
echo [%date% %time%] xinwenz done.
