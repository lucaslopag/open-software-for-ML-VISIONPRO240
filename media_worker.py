import time
import os
import cv2
from PIL import Image, ImageOps, ImageSequence
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
import shimeji_engine
import terraria_engine
import ultra_mc_engine
import masterpiece_mc_engine
import worldbox_engine
import streamlink

FRAME_SIZE = 8 + 480 * 480 * 3 + 8
CABECERA   = b'\xff\x00\x00\x00\x00\x1e\x01\xe0'
PIE        = b'\xff\xc0\x00\x00\x00\x00\x00\x00'

class MediaWorker(QThread):
    """
    Decodifica y procesa los medios (Imágenes, GIFs, MP4) a los FPS correctos.
    Genera el payload binario y se lo pasa al USB worker para transmisión.
    """
    preview_ready = Signal(QImage)
    
    def __init__(self, usb_worker, parent=None):
        super().__init__(parent)
        self.usb_worker = usb_worker
        self.running = False
        self.media_path = None
        self.rotation = 0
        self.scale_mode = "fit" # "fit" (recortar) o "stretch" (aplastar)
        
    def load_media(self, path):
        self.media_path = path

    def set_transform(self, rotation, scale_mode):
        self.rotation = rotation
        self.scale_mode = scale_mode

    def process_pil_frame(self, img):
        if self.rotation != 0:
            img = img.rotate(self.rotation, expand=True)
            
        if self.scale_mode == "fit":
            img = ImageOps.fit(img.convert('RGB'), (480, 480), Image.LANCZOS)
        else:
            img = img.convert('RGB').resize((480, 480), Image.LANCZOS)
            
        r, g, b = img.split()
        img_bgr = Image.merge('RGB', (b, g, r))
        
        pixeles = bytearray(img_bgr.tobytes())
        for i in range(len(pixeles)):
            if pixeles[i] == 0xff:
                pixeles[i] = 0xfe
                
        payload = CABECERA + bytes(pixeles) + PIE
        
        # Convert to QImage for UI preview (RGB mode)
        preview = img.convert("RGB")
        data = preview.tobytes("raw", "RGB")
        qimage = QImage(data, 480, 480, QImage.Format_RGB888)
        
        return payload, qimage

    def run(self):
        self.running = True
        
        while self.running:
            if not self.media_path or (self.media_path not in ['OBS_CAMERA', 'VIRTUAL_PET', 'TERRARIA_AI', 'ULTRA_MC', 'MASTERPIECE_MC', 'WORLDBOX_AI'] and not self.media_path.startswith('http') and not self.media_path.startswith('STREAM:') and not os.path.exists(self.media_path)):
                time.sleep(0.1)
                continue
                
            path = self.media_path
            
            # --- MASCOTA VIRTUAL ---
            if path == 'VIRTUAL_PET':
                engine = shimeji_engine.ShimejiEngine(fps=30)
                engine.start()
                interval = 1.0 / 30.0
                
                while self.running and self.media_path == path:
                    start_time = time.time()
                    pil_img = engine.get_frame()
                    payload, qimage = self.process_pil_frame(pil_img)
                    self.usb_worker.update_payload(payload)
                    self.preview_ready.emit(qimage)
                    elapsed = time.time() - start_time
                    time.sleep(max(0, interval - elapsed))
                engine.stop()
                
            # --- TERRARIA IA ---
            elif path == 'TERRARIA_AI':
                engine = terraria_engine.TerrariaEngine(fps=30)
                engine.start()
                interval = 1.0 / 30.0
                
                while self.running and self.media_path == path:
                    start_time = time.time()
                    pil_img = engine.get_frame()
                    payload, qimage = self.process_pil_frame(pil_img)
                    self.usb_worker.update_payload(payload)
                    self.preview_ready.emit(qimage)
                    elapsed = time.time() - start_time
                    time.sleep(max(0, interval - elapsed))
                engine.stop()

            # --- ULTRA MINECRAFT 2D ---
            elif path == 'ULTRA_MC':
                engine = ultra_mc_engine.UltraMCEngine(fps=30)
                engine.start()
                interval = 1.0 / 30.0
                
                while self.running and self.media_path == path:
                    start_time = time.time()
                    pil_img = engine.get_frame()
                    payload, qimage = self.process_pil_frame(pil_img)
                    self.usb_worker.update_payload(payload)
                    self.preview_ready.emit(qimage)
                    elapsed = time.time() - start_time
                    time.sleep(max(0, interval - elapsed))
                engine.stop()

            # --- MASTERPIECE MINECRAFT 2D ---
            elif path == 'MASTERPIECE_MC':
                engine = masterpiece_mc_engine.MasterpieceMCEngine(fps=30)
                engine.start()
                interval = 1.0 / 30.0
                
                while self.running and self.media_path == path:
                    start_time = time.time()
                    pil_img = engine.get_frame()
                    payload, qimage = self.process_pil_frame(pil_img)
                    self.usb_worker.update_payload(payload)
                    self.preview_ready.emit(qimage)
                    elapsed = time.time() - start_time
                    time.sleep(max(0, interval - elapsed))
                engine.stop()

            # --- WORLDBOX AI (UNITY HEADLESS) ---
            elif path == 'WORLDBOX_AI':
                engine = worldbox_engine.WorldboxEngine(fps=30)
                engine.start()
                interval = 1.0 / 30.0
                
                while self.running and self.media_path == path:
                    start_time = time.time()
                    pil_img = engine.get_frame()
                    payload, qimage = self.process_pil_frame(pil_img)
                    self.usb_worker.update_payload(payload)
                    self.preview_ready.emit(qimage)
                    elapsed = time.time() - start_time
                    time.sleep(max(0, interval - elapsed))
                engine.stop()
                
            # --- CÁMARA VIRTUAL OBS ---
            elif path == 'OBS_CAMERA':
                # Forzar el backend V4L2 para leer de la cámara de Linux
                cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L2)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
                    
                # Forzar 30 FPS si es posible
                cap.set(cv2.CAP_PROP_FPS, 30)
                fps = 30.0
                interval = 1.0 / fps
                
                while self.running and self.media_path == path:
                    start_time = time.time()
                    ret, frame = cap.read()
                    if not ret:
                        time.sleep(0.1)
                        continue
                        
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    
                    payload, qimage = self.process_pil_frame(pil_img)
                    self.usb_worker.update_payload(payload)
                    self.preview_ready.emit(qimage)
                    
                    elapsed = time.time() - start_time
                    time.sleep(max(0, interval - elapsed))
                cap.release()
                
            # --- DIRECTOS (TWITCH/YOUTUBE) ---
            elif path.startswith('STREAM:'):
                url = path.split('STREAM:', 1)[1]
                try:
                    streams = streamlink.streams(url)
                    if streams and "best" in streams:
                        stream_url = streams["best"].url
                        cap = cv2.VideoCapture(stream_url)
                        fps = 30.0
                        interval = 1.0 / fps
                        
                        while self.running and self.media_path == path:
                            start_time = time.time()
                            ret, frame = cap.read()
                            if not ret:
                                time.sleep(1)
                                cap.release()
                                cap = cv2.VideoCapture(stream_url)
                                continue
                                
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(frame_rgb)
                            
                            payload, qimage = self.process_pil_frame(pil_img)
                            self.usb_worker.update_payload(payload)
                            self.preview_ready.emit(qimage)
                            
                            elapsed = time.time() - start_time
                            time.sleep(max(0, interval - elapsed))
                        
                        cap.release()
                    else:
                        time.sleep(1)
                except Exception as e:
                    print(f"Error cargando stream: {e}")
                    time.sleep(1)
                
            # --- VIDEO MP4/AVI O CÁMARA IP (HTTP) ---
            elif path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm')) or (path.startswith('http') and not path.startswith('STREAM:')):
                cap = cv2.VideoCapture(path)
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                if fps <= 0: fps = 30.0
                interval = 1.0 / fps
                
                while self.running and self.media_path == path:
                    start_time = time.time()
                    ret, frame = cap.read()
                    if not ret:
                        if path.startswith('http'):
                            time.sleep(1)
                            cap.release()
                            cap = cv2.VideoCapture(path)
                        else:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                        
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    
                    payload, qimage = self.process_pil_frame(pil_img)
                    self.usb_worker.update_payload(payload)
                    self.preview_ready.emit(qimage)
                    
                    # Control de FPS
                    elapsed = time.time() - start_time
                    time.sleep(max(0, interval - elapsed))
                cap.release()
                
            # --- GIF ANIMADO ---
            elif path.lower().endswith('.gif'):
                try:
                    img = Image.open(path)
                    fps = 1000.0 / img.info.get('duration', 33.3)
                    interval = 1.0 / fps
                    
                    frames_cache = []
                    # Pre-cache if GIF is small enough to avoid disk IO during loop
                    # Real application might stream it if it's huge, but GIFs fit in RAM
                    
                    while self.running and self.media_path == path:
                        img.seek(0)
                        for frame in ImageSequence.Iterator(img):
                            if not self.running or self.media_path != path:
                                break
                            start_time = time.time()
                            
                            payload, qimage = self.process_pil_frame(frame)
                            self.usb_worker.update_payload(payload)
                            self.preview_ready.emit(qimage)
                            
                            elapsed = time.time() - start_time
                            time.sleep(max(0, interval - elapsed))
                except Exception as e:
                    print(f"Error reproduciendo GIF: {e}")
                    time.sleep(1)
                    
            # --- IMAGEN ESTÁTICA ---
            else:
                try:
                    img = Image.open(path)
                    # Loop lento para poder actualizar si cambia rotación/escala
                    while self.running and self.media_path == path:
                        payload, qimage = self.process_pil_frame(img)
                        self.usb_worker.update_payload(payload)
                        self.preview_ready.emit(qimage)
                        
                        # Comprobar cambios cada 100ms
                        for _ in range(10):
                            if not self.running or self.media_path != path: break
                            time.sleep(0.01)
                except Exception as e:
                    print(f"Error procesando imagen: {e}")
                    time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()
