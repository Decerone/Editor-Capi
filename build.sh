#!/bin/bash
echo "🚀 Construyendo Capi Editor Pro..."

# Limpiar builds anteriores
rm -rf build dist

# Compilar con PyInstaller (modo carpeta para mejor rendimiento en PySide6)
pyinstaller --noconfirm --onedir --windowed \
    --add-data "keywords.json:." \
    --add-data "config.json:." \
    --add-data "capieditor.png:." \
    --name "CapiEditor" \
    editor_app.py

echo "✅ Compilación terminada. El binario está en la carpeta 'dist/CapiEditor'."