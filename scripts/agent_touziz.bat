@echo off
chcp 65001 >nul
cd /d "c:\Users\hrgap\OneDrive\Desktop\2046孟之CC"
echo [%date% %time%] touziz starting...
python scripts/get_stock_data.py AAPL MSFT GOOGL AMZN META NVDA TSLA MU > temp_stock_data.txt 2>&1
powershell -ExecutionPolicy Bypass -File scripts\agent_touziz.ps1
echo [%date% %time%] touziz done.
