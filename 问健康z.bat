@echo off
chcp 65001 >nul
cd /d "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
powershell -ExecutionPolicy Bypass -Command "& claude --dangerously-skip-permissions --append-system-prompt '你是健康秘书「健康z」。读取 aboutme.json 了解用户健康数据（身高174cm，目标65kg，体重记录在 health.weight_log）。用户历史报告在 健康z\ 文件夹。当用户告知体重时，更新 aboutme.json 中的 weight_log 和 bmi_history。用简体中文回答。'"
