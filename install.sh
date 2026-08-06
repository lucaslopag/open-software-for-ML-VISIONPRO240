#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Instalador de Open Screen for Mars Gaming ==="
echo "Directorio de la app: $APP_DIR"

# 1. Crear entorno virtual si no existe
if [ ! -d "$APP_DIR/venv" ]; then
    echo "Creando entorno virtual de Python..."
    python3 -m venv "$APP_DIR/venv"
fi

# 2. Instalar dependencias
echo "Instalando dependencias desde requirements.txt..."
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# 3. Reglas udev (requiere sudo)
echo "Configurando permisos USB (requiere contraseña de administrador)..."
sudo bash -c 'echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"345f\", ATTRS{idProduct}==\"9132\", MODE=\"0666\"" > /etc/udev/rules.d/99-mars-gaming.rules'
sudo udevadm control --reload-rules
sudo udevadm trigger

# 4. Crear acceso directo en el escritorio (lanzador de aplicaciones Linux)
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
DESKTOP_FILE="$DESKTOP_DIR/open-screen-mars.desktop"

echo "Creando acceso directo en el menú de aplicaciones..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Open Screen for Mars Gaming
Comment=Controlador nativo para pantallas LCD Mars Gaming (MS9132)
Exec=$APP_DIR/run.sh
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;HardwareSettings;
EOF

chmod +x "$DESKTOP_FILE"
chmod +x "$APP_DIR/run.sh"

echo ""
echo "=== ¡Instalación Completada! ==="
echo "Ahora puedes abrir 'Open Screen for Mars Gaming' directamente desde tu menú de aplicaciones de Linux."
echo "Si quieres subir esto a GitHub, solo tienes que subir estos archivos. ¡Cualquiera podrá instalarlo ejecutando ./install.sh!"
