@echo off
chcp 65001 >nul
set /p TICKER=Stock ticker (e.g. NVDA TSLA AAPL):
if "%TICKER%"=="" (
    echo No ticker entered.
    pause
    exit /b
)
powershell -ExecutionPolicy Bypass -File "C:\Users\hrgap\OneDrive\Desktop\2046CC~1\scripts\ask_touzi_realtime.ps1" "%TICKER%"
pause
