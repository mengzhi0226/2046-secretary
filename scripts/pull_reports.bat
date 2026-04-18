@echo off
cd /d "c:\Users\hrgap\OneDrive\Desktop\2046孟之CC"
git pull origin main
echo [%date% %time%] Pull completed >> logs\pull.log
