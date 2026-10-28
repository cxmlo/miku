@echo off
setlocal enabledelayedexpansion
title Generador de Firma Keystore para Miku Android
color 0b

echo ========================================================
echo    MIKU ANDROID - GENERADOR DE FIRMA RELEASE (KEYSTORE)
echo ========================================================
echo.
echo Este script creara tu certificado oficial de firma SHA-256
echo y preparara el secreto para GitHub Actions automaticamente.
echo.

:: Verificar si keytool existe
where keytool >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se encontro 'keytool' en tu sistema.
    echo Asegurate de tener instalado Java JDK o Android Studio.
    echo.
    echo Si tienes Android Studio, suele estar en:
    echo "C:\Program Files\Android\Android Studio\jbr\bin"
    echo.
    pause
    exit /b 1
)

set KEY_ALIAS=miku
set KEYSTORE_FILE=miku-release.jks
set OUTPUT_BASE64=keystore_base64.txt

echo [1/4] Elige una contrasena segura para tu clave:
set /p KEY_PASS="Introduce la contrasena (ej. MikuSecureKey2026): "
if "%KEY_PASS%"=="" (
    echo No introdujiste contrasena. Usando una por defecto: MikuSecret2026!
    set KEY_PASS=MikuSecret2026!
)

echo.
echo [2/4] Generando certificado criptografico de 2048 bits...
if exist "%KEYSTORE_FILE%" del "%KEYSTORE_FILE%"

keytool -genkey -v -keystore "%KEYSTORE_FILE%" -alias %KEY_ALIAS% -keyalg RSA -keysize 2048 -validity 10000 -storepass "%KEY_PASS%" -keypass "%KEY_PASS%" -dname "CN=Miku Mobile, OU=Desktop Companion, O=Miku Project, L=Local, ST=State, C=US"

if not exist "%KEYSTORE_FILE%" (
    echo [ERROR] No se pudo generar el archivo %KEYSTORE_FILE%.
    pause
    exit /b 1
)

echo.
echo [3/4] Convirtiendo certificado a Base64 para GitHub Secrets...
certutil -encode "%KEYSTORE_FILE%" "%OUTPUT_BASE64%" >nul 2>&1

:: Limpiar encabezados que genera certutil
powershell -Command "$content = Get-Content '%OUTPUT_BASE64%' | Where-Object { $_ -notmatch '-----' }; Set-Content '%OUTPUT_BASE64%' ($content -join '')"

:: Copiar al portapapeles automaticamente
type "%OUTPUT_BASE64%" | clip 2>nul
echo [OK] Archivo generado: %OUTPUT_BASE64%
echo [OK] El texto Base64 ya esta COPIADO en tu portapapeles.

echo.
echo ========================================================
echo   CONFIGURACION EN GITHUB REPOSITORY (Settings > Secrets)
echo ========================================================
echo.
echo Ve a tu repositorio en GitHub:
echo https://github.com/cxmlo/miku/settings/secrets/actions
echo.
echo Pulsa "New repository secret" y anade estos 4 secretos:
echo.
echo 1. Nombre: KEYSTORE_BASE64
echo    Valor:  [Pega aqui lo que ya tienes copiado en el portapapeles]
echo.
echo 2. Nombre: KEYSTORE_PASSWORD
echo    Valor:  %KEY_PASS%
echo.
echo 3. Nombre: KEY_ALIAS
echo    Valor:  %KEY_ALIAS%
echo.
echo 4. Nombre: KEY_PASSWORD
echo    Valor:  %KEY_PASS%
echo.
echo ========================================================
echo Guarda el archivo '%KEYSTORE_FILE%' en un lugar seguro.
echo (Esta protegido y bloqueado en .gitignore para no subirse al repo).
echo.
pause
