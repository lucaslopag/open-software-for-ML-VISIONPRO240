import time
import usb.core
import sys
import os
from PIL import Image, ImageSequence
from init_cmds import INIT_COMMANDS

# =====================================================================
# PROTOCOLO ML-VISIONPRO240 / MacroSilicon MS9132
# - Chip: MS9132 (USB HID + Bulk transfer)
# - Resolución: 480x480 px
# - Formato de pixel: BGR888 (3 bytes por pixel), sin 0xFF en los datos
# - Frame completo: 8 bytes cabecera + 480*480*3 bytes pixels + 8 bytes pie
# - Total bytes por frame = 691216 bytes
# =====================================================================

VID, PID = 0x345F, 0x9132
FRAME_SIZE = 8 + 480 * 480 * 3 + 8  # 691216 bytes exactos
CABECERA   = b'\xff\x00\x00\x00\x00\x1e\x01\xe0'
PIE        = b'\xff\xc0\x00\x00\x00\x00\x00\x00'

def conectar_pantalla():
    print("Buscando pantalla ML-VISIONPRO240...")
    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if not dev:
        sys.exit("Error: Pantalla no encontrada. Asegúrate de tener permisos o usar sudo.")
    try:
        if dev.is_kernel_driver_active(0): 
            dev.detach_kernel_driver(0)
    except: pass
    try: dev.set_configuration()
    except: pass
    return dev

def inicializar(dev):
    print("Inicializando pantalla (enviando handshake)...")
    for f in INIT_COMMANDS:
        try:
            dev.ctrl_transfer(
                f['bmRequestType'], f['bRequest'], f['wValue'], 
                f['wIndex'], f['data_or_len'], timeout=100
            )
        except Exception: pass
        time.sleep(0.005)
    
    print("Esperando 1 segundo para que el panel LCD despierte...")
    time.sleep(1.0)

def heartbeat(dev):
    """Mantiene vivo el watchdog de la pantalla entre frames"""
    for bm, br, d in [
        (0x21, 0x09, bytes.fromhex('b500320000000000')),
        (0xa1, 0x01, 8),
        (0x21, 0x09, bytes.fromhex('b500320000000000')),
        (0xa1, 0x01, 8)
    ]:
        try: dev.ctrl_transfer(bm, br, 0x0300, 0, d, timeout=100)
        except: pass
from PIL import Image, ImageSequence, ImageDraw, ImageOps

def procesar_frame(img):
    """Convierte una imagen PIL a los bytes binarios exactos del MS9132"""
    # Usar resize para aplastar/estirar la imagen y que se vea completa sin recortar bordes
    img = img.convert('RGB').resize((480, 480), Image.LANCZOS)
    
    # BGR format
    r, g, b = img.split()
    img_bgr = Image.merge('RGB', (b, g, r))
    
    pixeles = bytearray(img_bgr.tobytes())
    
    # Sustituir 0xFF por 0xFE (0xFF es comando de control)
    for i in range(len(pixeles)):
        if pixeles[i] == 0xff:
            pixeles[i] = 0xfe

    return CABECERA + bytes(pixeles) + PIE

from PIL import Image, ImageSequence, ImageDraw

def cargar_media(ruta):
    frames_bytes = []
    fps = 30
    
    if not os.path.exists(ruta):
        print(f"Generando patrón de prueba porque no existe {ruta}...")
        img = Image.new('RGB', (480, 480), color=(254, 0, 0))
        draw = ImageDraw.Draw(img)
        # Dibujar un rectángulo azul
        draw.rectangle([100, 100, 380, 380], fill=(0, 0, 254))
        # Dibujar un cuadrado amarillo en el centro
        draw.rectangle([150, 150, 330, 330], fill=(254, 254, 0))
        
        # Añadir texto
        try:
            from PIL import ImageFont
            # Intentar usar una fuente por defecto más grande si es posible
            font = ImageFont.load_default()
            
            texto = "MARS GAMING LCD\n100% LINUX NATIVE\nDRIVER BY ANTIGRAVITY"
            # bbox devuelve (left, top, right, bottom)
            bbox = draw.multiline_textbbox((0, 0), texto, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (480 - text_width) // 2
            y = (480 - text_height) // 2
            draw.multiline_text((x, y), texto, fill=(0, 0, 0), font=font, align="center")
        except Exception as e:
            print("No se pudo dibujar texto:", e)
            
        frames_bytes.append(procesar_frame(img))
        return frames_bytes, fps

    print(f"Procesando {ruta}...")
    img = Image.open(ruta)
    
    # Detectar si es un GIF animado
    if getattr(img, "is_animated", False):
        fps = 1000 / img.info.get('duration', 33.3)
        print(f"GIF detectado: {img.n_frames} frames a ~{fps:.1f} FPS")
        for i, frame in enumerate(ImageSequence.Iterator(img)):
            frames_bytes.append(procesar_frame(frame))
    else:
        frames_bytes.append(procesar_frame(img))
        
    return frames_bytes, fps

def main():
    archivo = sys.argv[1] if len(sys.argv) > 1 else 'imagen.jpg'
    
    # 1. Preparar las imagenes (así no hay delay en tiempo real)
    frames_data, fps = cargar_media(archivo)
    intervalo = 1.0 / fps

    # 2. Conectar e Inicializar
    dev = conectar_pantalla()
    inicializar(dev)
    
    # 3. Primer latido para desbloquear la recepción de video
    heartbeat(dev)

    # 4. Bucle de Reproducción
    print(f"\n>>> Reproduciendo en pantalla... (Ctrl+C para salir) <<<")
    try:
        idx = 0
        while True:
            inicio = time.time()
            
            # Enviar frame en UN SOLO block transfer (requiere usbfs_memory_mb alto)
            dev.write(0x04, frames_data[idx], timeout=5000)
            heartbeat(dev)
            
            # Control de animación
            idx = (idx + 1) % len(frames_data)
            
            # Sincronizar FPS
            tiempo_transcurrido = time.time() - inicio
            espera = intervalo - tiempo_transcurrido
            if espera > 0:
                time.sleep(espera)
                
    except KeyboardInterrupt:
        print("\nReproducción detenida.")
    except Exception as e:
        print(f"\nError durante la reproducción: {e}")

if __name__ == '__main__':
    main()
