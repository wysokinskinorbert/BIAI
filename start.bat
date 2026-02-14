@echo off
title BIAI - Business Intelligence AI
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
pause
