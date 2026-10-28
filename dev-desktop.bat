@echo off
title Miku Desktop UI (Tauri Dev con Hot-Reload)
echo ====================================================
echo  Iniciando Miku Desktop UI en modo desarrollo...
echo  (Hot-Reload de HTML/JS/CSS y F12 para DevTools)
echo ====================================================
cd /d "%~dp0miku_ui"
npm run tauri dev
pause
