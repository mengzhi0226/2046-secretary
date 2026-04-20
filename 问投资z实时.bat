@echo off
chcp 65001 >nul
echo.
echo  ==========================================
echo   投资z  实时盘前查询
echo  ==========================================
echo.
set /p TICKER=  请输入股票代码 (如 NVDA TSLA AAPL):
echo.
if "%TICKER%"=="" (
    echo  未输入代码，退出。
    pause
    exit /b
)
echo  正在查询 %TICKER%，请稍候约30-60秒...
echo.
powershell -ExecutionPolicy Bypass -File "C:\Users\hrgap\OneDrive\Desktop\2046CC~1\scripts\ask_touzi_realtime.ps1" "%TICKER%"
pause
