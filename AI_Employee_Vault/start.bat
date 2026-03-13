@echo off
REM AI Employee - Bronze Tier Startup Script
REM This script starts both the Filesystem Watcher and Orchestrator

echo ============================================
echo   AI Employee v0.1 - Bronze Tier
echo ============================================
echo.

cd /d "%~dp0"

echo Starting Filesystem Watcher...
start "AI Employee - Watcher" cmd /k "cd scripts && python filesystem_watcher.py"

timeout /t 2 /nobreak >nul

echo Starting Orchestrator...
start "AI Employee - Orchestrator" cmd /k "cd scripts && python orchestrator.py"

echo.
echo ============================================
echo   Both services started!
echo.
echo   To stop: Close the terminal windows
echo   To test: Drop a file in the Inbox folder
echo ============================================
echo.

REM Open the vault folder
explorer ".."
