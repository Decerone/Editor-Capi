#!/bin/bash

# --- CONFIGURACIÓN ---
APP_NAME="capi_editor"
INSTALL_DIR="/opt/$APP_NAME"
# Nombre exacto de tu archivo python
MAIN_SCRIPT="editor_app.py" 
# Nombre exacto de tu icono
ICON_FILE="icon.png"

echo "🔧 Instalando Capi Editor..."

# 1. Crear el directorio en /opt
sudo mkdir -p $INSTALL_DIR

# 2. Copiar TODOS los archivos de tu carpeta actual a /opt
# Esto asegura que el icono y el script se vayan juntos
sudo cp -r . $INSTALL_DIR

# 3. Dar permisos de ejecución
sudo chmod +x $INSTALL_DIR/$MAIN_SCRIPT

# 4. Crear el archivo .desktop apuntando a las rutas exactas
# ATENCIÓN: Aquí definimos la ruta absoluta del icono
cat <<EOF > $APP_NAME.desktop
[Desktop Entry]
Name=Capi Editor
Comment=Mi editor de código
Exec=python3 $INSTALL_DIR/$MAIN_SCRIPT
Icon=$INSTALL_DIR/$ICON_FILE
Terminal=false
Type=Application
Categories=Development;
StartupNotify=true
StartupWMClass=capi_editor
StartupWMClass=$MAIN_SCRIPT
EOF

# 5. Mover el acceso directo al sistema
sudo mv $APP_NAME.desktop /usr/share/applications/

# 6. Actualizar la caché de iconos del sistema (TRUCO IMPORTANTE)
sudo update-desktop-database

echo "✅ Instalado. Busca 'Capi Editor' en tu menú."