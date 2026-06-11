@echo off
chcp 65001 >nul
title Nghien Netflix - Server
cd /d "%~dp0"
echo ================================================
echo    NGHIEN NETFLIX - Dang khoi dong server...
echo ================================================
echo.
python server.py
if errorlevel 1 (
  echo.
  echo [LOI] Khong chay duoc. Kiem tra da cai Python chua?
  echo Tai Python tai: https://www.python.org/downloads/
  pause
)
