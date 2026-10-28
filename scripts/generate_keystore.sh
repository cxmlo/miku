#!/usr/bin/env bash
set -e

echo "========================================================"
echo "   MIKU ANDROID - GENERADOR DE FIRMA RELEASE (KEYSTORE)"
echo "========================================================"
echo ""

KEY_ALIAS="miku"
KEYSTORE_FILE="miku-release.jks"
OUTPUT_BASE64="keystore_base64.txt"

read -s -p "Introduce una contraseña para el keystore: " KEY_PASS
echo ""

if [ -z "$KEY_PASS" ]; then
    KEY_PASS="MikuSecret2026!"
    echo "Usando contraseña por defecto: $KEY_PASS"
fi

rm -f "$KEYSTORE_FILE" "$OUTPUT_BASE64"

echo "[1/3] Generando certificado oficial con keytool..."
keytool -genkey -v -keystore "$KEYSTORE_FILE" -alias "$KEY_ALIAS" -keyalg RSA -keysize 2048 -validity 10000 -storepass "$KEY_PASS" -keypass "$KEY_PASS" -dname "CN=Miku Mobile, OU=Companion, O=Miku Project, L=Local, ST=State, C=US"

echo "[2/3] Convirtiendo a Base64..."
if command -v base64 >/dev/null 2>&1; then
    base64 -w 0 "$KEYSTORE_FILE" > "$OUTPUT_BASE64" 2>/dev/null || base64 -i "$KEYSTORE_FILE" -o "$OUTPUT_BASE64"
fi

echo "[3/3] Listo. Archivo generado: $OUTPUT_BASE64"
echo ""
echo "========================================================"
echo "  CONFIGURACIÓN EN GITHUB (Settings > Secrets > Actions)"
echo "========================================================"
echo "1. KEYSTORE_BASE64   -> Contenido de $OUTPUT_BASE64"
echo "2. KEYSTORE_PASSWORD -> $KEY_PASS"
echo "3. KEY_ALIAS         -> $KEY_ALIAS"
echo "4. KEY_PASSWORD      -> $KEY_PASS"
echo "========================================================"
