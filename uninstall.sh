#!/bin/bash

# Colores para la terminal
RED='\033[0;31m'
NC='\033[0m' # No Color
GREEN='\033[0;32m'

echo -e "${RED}Iniciando la desinstalación de capi_editor...${NC}"

# 1. Eliminar el binario/ejecutable principal
if [ -f "/usr/local/bin/capi_editor" ]; then
    sudo rm /usr/local/bin/capi_editor
    echo "✔ Ejecutable eliminado de /usr/local/bin"
fi

# 2. Eliminar la carpeta del código fuente/recursos (si existe en /opt)
if [ -d "/opt/capi_editor" ]; then
    sudo rm -rf /opt/capi_editor
    echo "✔ Carpeta de aplicación en /opt eliminada"
fi

# 3. Eliminar el acceso directo del menú de aplicaciones (.desktop)
if [ -f "$HOME/.local/share/applications/capi_editor.desktop" ]; then
    rm "$HOME/.local/share/applications/capi_editor.desktop"
    echo "✔ Acceso directo de usuario eliminado"
fi

if [ -f "/usr/share/applications/capi_editor.desktop" ]; then
    sudo rm /usr/share/applications/capi_editor.desktop
    echo "✔ Acceso directo del sistema eliminado"
fi

# 4. Eliminar archivos de configuración del usuario
if [ -d "$HOME/.config/capi_editor" ]; then
    rm -rf "$HOME/.config/capi_editor"
    echo "✔ Configuraciones de usuario eliminadas"
fi

echo -e "${GREEN}Desinstalación completada con éxito.${NC}"