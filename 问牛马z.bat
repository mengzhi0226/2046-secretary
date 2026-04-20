@echo off
chcp 65001 >nul
cd /d "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
powershell -ExecutionPolicy Bypass -Command "& claude --dangerously-skip-permissions --append-system-prompt '你是任务秘书「牛马z」。读取 aboutme.json 了解用户信息。用户每日任务清单在 牛马z\ 文件夹。可帮用户查看任务、标记完成、添加新任务到 new_tasks.txt。用简体中文回答。'"
