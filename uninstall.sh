#!/bin/bash

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Por favor, ejecuta este script como administrador (sudo ./uninstall.sh)"
  exit 1
fi

echo "🗑️ Desinstalando Capi Editor Pro..."

# 1. Borrar la carpeta principal
rm -rf /opt/capieditor

# 2. Borrar el enlace simbólico
rm -f /usr/local/bin/capi

# 3. Borrar el icono del sistema
rm -f /usr/share/pixmaps/capieditor.png

# 4. Borrar la entrada del menú de aplicaciones
rm -f /usr/share/applications/capi-editor.desktop

# 5. Borrar el acceso directo del Escritorio de los usuarios (Español e Inglés)
rm -f /home/*/Escritorio/capi-editor.desktop 2>/dev/null
rm -f /home/*/Desktop/capi-editor.desktop 2>/dev/null

# 6. Actualizar la base de datos del escritorio
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications/
fi

echo "✅ Capi Editor ha sido eliminado completamente del sistema."