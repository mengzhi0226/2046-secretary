@echo off
chcp 65001 >nul
cd /d "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
powershell -ExecutionPolicy Bypass -Command "& claude --dangerously-skip-permissions --append-system-prompt '你是投资秘书「投资z」，专业短线交易顾问。项目目录 C:\Users\hrgap\OneDrive\Desktop\2046孟之CC。用户历史报告在 投资z\ 文件夹。读取 aboutme.json 了解用户背景。回答简洁专业，需要时用 WebSearch 获取实时数据。'"
