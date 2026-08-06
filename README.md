# Open Screen for Mars Gaming (ML-VISIONPRO240) 🚀

![Mars Gaming Liquid Cooling LCD](https://img.shields.io/badge/Hardware-Mars_Gaming_ML--VISIONPRO240-red.svg)
![Chipset](https://img.shields.io/badge/Chipset-MacroSilicon_MS9132-blue.svg)
![OS](https://img.shields.io/badge/OS-Linux_Native-green.svg)

*(Scroll down for Spanish / Desplázate hacia abajo para Español)*

## 🇬🇧 English: Native Linux Driver & GUI for Mars Gaming LCDs

An **open-source, native Linux GUI controller** for the LCD screens built into **Mars Gaming Liquid Coolers (MacroSilicon MS9132 Chipset)**, specifically designed to solve the lack of Linux support for models like the **ML-VISIONPRO240**.

Designed from scratch to bypass proprietary Windows software. It runs independently and ultra-smoothly using PySide6 (Qt) and PyUSB.

### ✨ Features
*   **Full Media Support:** Play static images (`.jpg`, `.png`), GIF animations (`.gif`), and real video files (`.mp4`, `.avi`, `.mkv`) on the fly via OpenCV without bloating your RAM.
*   **Real-time Controls:** 
    *   **Rotation:** Rotate the screen 0º, 90º, 180º, or 270º instantly (perfect if you mounted the pump block upside down).
    *   **Scaling:** Crop (keep aspect ratio) or Stretch to 480x480.
*   **OBS Studio Virtual Camera Integration:** Want to use the tiny LCD as a secondary monitor to display PC temperatures (MangoHud, Conky), web browsers, or games on Linux Wayland? Connect it to the **OBS Studio Virtual Camera** with one click and stream any window at 30 FPS!
*   **Safe Multi-Threading:** The GUI, video decoder, and low-level USB communication run on completely separate threads. The app never freezes.
*   **Root-less Execution:** Includes automated `udev` rules so you can run the program as a normal user.

### 📦 Easy Installation
1. Clone this repository.
2. Run the installer:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. The installer will set up a Python virtual environment, install dependencies, configure USB permissions, and create a Linux Desktop Shortcut for you.

---

## 🇪🇸 Español: Controlador Nativo para Pantallas Mars Gaming en Linux

Un controlador **nativo para Linux y de código abierto (Open Source)** para las pantallas LCD integradas en las refrigeraciones líquidas de **Mars Gaming (Chipset MacroSilicon MS9132)**, como el modelo **ML-VISIONPRO240**.

Diseñado desde cero para saltarse las dependencias privativas de Windows. Funciona de manera independiente y ultra-fluida mediante PySide6 (Qt) y PyUSB.

### ✨ Características Principales
*   **Soporte Total de Medios:** Reproduce imágenes estáticas (`.jpg`, `.png`), animaciones GIF (`.gif`) y vídeos reales (`.mp4`, `.avi`, `.webm`) al vuelo mediante OpenCV, sin saturar tu memoria RAM.
*   **Ajustes en Tiempo Real:** 
    *   **Rotación:** Gira la pantalla 0º, 90º, 180º o 270º instantáneamente (ideal si has montado el bloque de la bomba al revés).
    *   **Escalado:** Modos de *Recorte* (para mantener proporciones) o *Aplastar* (estirar a 480x480).
*   **Integración con OBS Studio (Monitor Extra):** ¿Quieres usar la pantallita como un monitor secundario para monitorizar temperaturas, mostrar navegadores o juegos en Linux Wayland? Conéctala a la **Cámara Virtual de OBS Studio** con un solo clic y transmite cualquier ventana o lienzo a 30 FPS.
*   **Arquitectura Multi-Hilo Segura:** La interfaz gráfica (GUI), el decodificador de vídeo y la comunicación USB de bajo nivel corren en hilos totalmente separados. ¡La aplicación nunca se congela!
*   **Sin Privilegios de Root:** Incluye reglas `udev` automáticas para que puedas ejecutar el programa como un usuario normal.

### 📦 Instalación Fácil
Hemos creado un instalador automático que preparará el entorno, instalará las dependencias necesarias de Python y configurará los permisos USB (`udev`) por ti.

1. Abre tu terminal y clona o descarga esta carpeta.
2. Navega al directorio del proyecto y ejecuta el instalador:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. El instalador te pedirá tu contraseña (solo una vez) para instalar las reglas de permisos USB.
4. **¡Listo!** El instalador creará un acceso directo nativo en tu menú de aplicaciones de Linux.

---

### 🛠️ Hardware Info / Technical Details
The MS9132 hardware requires an extremely strict initialization sequence of 252 *Control Transfer* commands to boot the LCD panel, followed by a constant *Bulk Transfer* data injection of 691,216 bytes (480x480 frame + header/footer) at 30 FPS. It also requires a continuous *heartbeat*; otherwise, the hardware watchdog will reset the screen to the factory logo. This software handles the entire protocol asynchronously.

*Tags: Mars Gaming, ML-VISIONPRO240, ML-VISION PRO 240, Linux Driver, MS9132, MacroSilicon, AIO LCD Screen, Water Cooling Display, Open Source.*
