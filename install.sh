#!/bin/bash

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Por favor, ejecuta este script como administrador (sudo ./install.sh)"
  exit 1
fi

# Verificar si el binario existe antes de instalar
if [ ! -d "dist/CapiEditor" ]; then
  echo "❌ Error: No se encontró la carpeta dist/CapiEditor. Asegúrate de compilar primero."
  exit 1
fi

echo "📦 Instalando Capi Editor Pro..."

# 1. Copiar los binarios a /opt
mkdir -p /opt/capieditor
cp -r dist/CapiEditor/* /opt/capieditor/
chmod +x /opt/capieditor/CapiEditor

# 2. Crear un enlace simbólico (comando 'capi' en terminal)
ln -sf /opt/capieditor/CapiEditor /usr/local/bin/capi

# 3. Instalar el ícono
cp capieditor.png /usr/share/pixmaps/capieditor.png
chmod 644 /usr/share/pixmaps/capieditor.png

# 4. Instalar en el menú de aplicaciones
cp capi-editor.desktop /usr/share/applications/
chmod 644 /usr/share/applications/capi-editor.desktop

# 5. Crear acceso directo en el Escritorio del usuario real
if [ -n "$SUDO_USER" ]; then
    # Obtener la ruta real del usuario que ejecutó sudo
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    
    # Detectar si usa el sistema en Español o Inglés
    if [ -d "$USER_HOME/Escritorio" ]; then
        DESKTOP_DIR="$USER_HOME/Escritorio"
    elif [ -d "$USER_HOME/Desktop" ]; then
        DESKTOP_DIR="$USER_HOME/Desktop"
    else
        DESKTOP_DIR=""
    fi

    # Copiar y asignar permisos si se encontró la carpeta
    if [ -n "$DESKTOP_DIR" ]; then
        cp capi-editor.desktop "$DESKTOP_DIR/"
        # Hacerlo ejecutable para que no pida confirmación al abrir
        chmod +x "$DESKTOP_DIR/capi-editor.desktop"
        # Devolverle la propiedad al usuario (quitarle el candado de root)
        chown "$SUDO_USER:$SUDO_USER" "$DESKTOP_DIR/capi-editor.desktop"
        echo "📄 Acceso directo creado en el Escritorio."
    fi
fi

# 6. Actualizar las bases de datos del sistema
echo "🔄 Refrescando el caché del sistema..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications/
fi

if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor/ &> /dev/null
fi

echo "✅ ¡Instalación completada con éxito!"