@echo off
chcp 65001 >nul
cd /d "c:\Users\hrgap\OneDrive\Desktop\2046孟之CC"
echo [%date% %time%] niumaz starting...
powershell -ExecutionPolicy Bypass -File scripts\agent_niumaz.ps1
echo [%date% %time%] niumaz done.
