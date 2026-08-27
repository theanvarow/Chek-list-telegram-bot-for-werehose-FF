@echo off
cd /d "%~dp0"
title Telegram Checklist Bot Manager
echo ===================================================
echo Telegram Checklist Bot (Auto-Restart Manager)
echo ===================================================
win_venv\Scripts\python.exe run_bot.py
pause
