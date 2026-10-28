@echo off
title Lanzador de Desarrollo Miku V2
echo ====================================================
echo  Iniciando Entorno de Desarrollo Miku V2...
echo  Ventana 1: Servidor Python con Logs en vivo
echo  Ventana 2: Aplicacion de Escritorio Tauri Dev
echo ====================================================
cd /d "%~dp0"
start "Miku Core Server" cmd /k dev-server.bat
timeout /t 2 /nobreak >nul
start "Miku Desktop Dev" cmd /k dev-desktop.bat
exit
