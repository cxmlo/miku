@echo off
title Miku Core Backend (Modo Desarrollo con Logs)
echo ====================================================
echo  Iniciando Miku Core Backend en modo consola...
echo  (Veras todos los logs, peticiones y errores en vivo)
echo ====================================================
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe server.py
) else (
    python server.py
)
pause
