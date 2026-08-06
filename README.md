# Open Screen for Mars Gaming 🚀

Un controlador **nativo para Linux**, moderno y de código abierto (Open Source) para las pantallas LCD integradas en las refrigeraciones líquidas de **Mars Gaming (Chipset MacroSilicon MS9132)**, como el modelo ML-VISIONPRO240.

Diseñado desde cero para saltarse las dependencias privativas de Windows. Funciona de manera independiente y ultra-fluida mediante PySide6 (Qt) y PyUSB.

---

## ✨ Características Principales

*   **Soporte Total de Medios:** Reproduce imágenes estáticas (`.jpg`, `.png`), animaciones GIF (`.gif`) y vídeos reales (`.mp4`, `.avi`, `.webm`) al vuelo mediante OpenCV, sin saturar tu memoria RAM.
*   **Ajustes en Tiempo Real:** 
    *   **Rotación:** Gira la pantalla 0º, 90º, 180º o 270º instantáneamente (ideal si has montado el bloque de la bomba al revés).
    *   **Escalado:** Modos de *Recorte* (para mantener proporciones perfectas) o *Aplastar* (estirar a 480x480).
*   **Integración con OBS Studio (¡NUEVO!):** ¿Quieres usar la pantallita como un monitor secundario para monitorizar temperaturas, mostrar navegadores o juegos en Linux Wayland? Conéctala a la **Cámara Virtual de OBS Studio** con un solo clic y transmite cualquier ventana o lienzo a 30 FPS.
*   **Arquitectura Multi-Hilo Segura:** La interfaz gráfica (GUI), el decodificador de vídeo y la comunicación USB de bajo nivel corren en hilos totalmente separados. ¡La aplicación nunca se congela!
*   **Sin Privilegios de Root:** Incluye reglas `udev` automáticas para que puedas ejecutar el programa como un usuario normal.

---

## 📦 Instalación Fácil (Para cualquier ordenador Linux)

Hemos creado un instalador automático que preparará el entorno, instalará las dependencias necesarias de Python y configurará los permisos USB (`udev`) por ti.

1. Abre tu terminal y clona o descarga esta carpeta.
2. Navega al directorio del proyecto y ejecuta el instalador:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. El instalador te pedirá tu contraseña (solo una vez) para instalar las reglas de permisos USB en tu sistema operativo.
4. **¡Listo!** El instalador creará un acceso directo nativo en tu menú de aplicaciones de Linux. Ya puedes buscar **"Open Screen for Mars Gaming"** en el lanzador de tu escritorio y abrirlo con un clic.

---

## 🛠️ Cómo Funciona la Magia (Para Desarrolladores)

El hardware MS9132 requiere una secuencia de inicialización extremadamente estricta de 252 comandos *Control Transfer* para arrancar el panel LCD, seguida de una inyección de datos *Bulk Transfer* constante de 691.216 bytes (frame de 480x480 + cabecera/pie) a 30 FPS. Además, requiere un *heartbeat* (latido de mantenimiento) continuo, de lo contrario, el watchdog de hardware reiniciará la pantalla al logo de fábrica.

*Open Screen for Mars Gaming* maneja todo esto automáticamente en el archivo `usb_worker.py`.

### Requisitos Manuales (Si no usas el instalador)
- Python 3.10+
- `pip install -r requirements.txt`
- Regla Udev: `SUBSYSTEM=="usb", ATTRS{idVendor}=="345f", ATTRS{idProduct}=="9132", MODE="0666"`

---

## 💻 El "Modo Monitor Extra" usando OBS Studio (Wayland)

Dada la estricta seguridad de Wayland en Linux moderno (Bazzite, Fedora, Ubuntu), capturar la pantalla y enviarla a un dispositivo USB directamente es complejo. Por ello, delegamos el "trabajo sucio" a OBS Studio:

1. Instala **OBS Studio** en tu Linux.
2. Abre OBS, añade una fuente (ej. *Captura de Pantalla PipeWire*, *Captura de Ventana*, o un texto).
3. Haz clic en **"Iniciar Cámara Virtual"** en los controles de OBS.
4. Abre nuestra app y pulsa el botón rojo **"🎥 Conectar a OBS Virtual Camera"**.
5. Disfruta de un lienzo completamente personalizable. *(Recomendación: Configura el lienzo de OBS a resolución 480x480 o 1080x1080 para evitar distorsiones).*

---

*Proyecto creado por la comunidad, para la comunidad. Si te ha sido útil, ¡no dudes en dejar una estrella en el repositorio! ⭐*
