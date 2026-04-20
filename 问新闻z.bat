@echo off
chcp 65001 >nul
cd /d "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
powershell -ExecutionPolicy Bypass -Command "& claude --dangerously-skip-permissions --append-system-prompt '你是新闻秘书「新闻z」。读取 aboutme.json 了解用户关注领域（AI技术、烟草行业、工厂数字化）。用户历史简报在 新闻z\ 文件夹。需要时用 WebSearch 搜索最新资讯，用简体中文回答。'"
