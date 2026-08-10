import os
import time
import subprocess
import threading
import random
from PIL import Image
import mss
import signal

class WorldboxEngine:
    def __init__(self, fps=30):
        self.fps = fps
        self.running = False
        self.xvfb_proc = None
        self.wb_proc = None
        self.ai_thread = None
        
    def start(self):
        self.running = True
        # Iniciar Monitor Fantasma
        print("[WorldBox] Iniciando Xvfb en :99...")
        self.xvfb_proc = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "480x480x24"])
        time.sleep(1) # Esperar a que el servidor X inicie
        
        # Iniciar WorldBox atrapado en :99
        print("[WorldBox] Iniciando binario de Unity...")
        env = os.environ.copy()
        env["DISPLAY"] = ":99"
        
        # Forzamos resolución por si acaso
        cmd = [
            "./worldbox/worldbox", 
            "-screen-width", "480", 
            "-screen-height", "480", 
            "-screen-fullscreen", "0"
        ]
        self.wb_proc = subprocess.Popen(cmd, env=env)
        
        # Iniciar Capturador
        self.sct = mss.mss(display=":99")
        
        # Iniciar IA Poltergeist
        self.ai_thread = threading.Thread(target=self.ai_loop)
        self.ai_thread.daemon = True
        self.ai_thread.start()

    def xdo(self, *args):
        env = os.environ.copy()
        env["DISPLAY"] = ":99"
        subprocess.run(["xdotool"] + list(args), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def ai_loop(self):
        time.sleep(8) # Esperar a que el juego cargue
        
        # La interfaz de WorldBox está en los bordes.
        # Coordenadas aproximadas para 480x480:
        # Pestañas inferiores (Naturaleza, Civilizaciones, Animales, Destrucción)
        
        tabs = [
            (100, 450), # Naturaleza
            (180, 450), # Civilizaciones
            (260, 450), # Animales
            (340, 450)  # Destrucción / Bombas
        ]
        
        while self.running:
            # Seleccionar una pestaña al azar
            tx, ty = random.choice(tabs)
            self.xdo("mousemove", str(tx), str(ty), "click", "1")
            time.sleep(1.0)
            
            # Hacer clics aleatorios en el menú secundario (que aparece encima de las pestañas)
            for _ in range(3):
                sx = random.randint(50, 430)
                sy = random.randint(380, 420)
                self.xdo("mousemove", str(sx), str(sy), "click", "1")
                time.sleep(0.5)
                
            # Espamear la herramienta seleccionada en el mapa
            for _ in range(10):
                if not self.running: break
                mx = random.randint(50, 430)
                my = random.randint(50, 350)
                
                # Simular click presionado o rápido
                self.xdo("mousemove", str(mx), str(my), "mousedown", "1")
                time.sleep(0.2)
                self.xdo("mousemove", str(mx + random.randint(-20, 20)), str(my + random.randint(-20, 20)))
                self.xdo("mouseup", "1")
                
                time.sleep(0.5)
                
            # A veces hacer scroll/arrastrar cámara
            if random.random() < 0.3:
                self.xdo("mousemove", "240", "240", "mousedown", "3") # Clic derecho
                self.xdo("mousemove_relative", "--", str(random.randint(-100, 100)), str(random.randint(-100, 100)))
                self.xdo("mouseup", "3")
                time.sleep(1.0)

    def get_frame(self):
        if not self.running:
            return Image.new('RGB', (480, 480), (0,0,0))
            
        try:
            # Capturar el monitor 1 (el único que hay en Xvfb)
            monitor = self.sct.monitors[1]
            sct_img = self.sct.grab(monitor)
            # mss devuelve BGRA, convertimos a RGB para Pillow
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            # Si el juego todavía no ha creado la ventana o hay fallo
            return Image.new('RGB', (480, 480), (0,0,0))

    def stop(self):
        self.running = False
        print("[WorldBox] Matando procesos...")
        if self.wb_proc:
            self.wb_proc.terminate()
            try:
                self.wb_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.wb_proc.kill()
        
        if self.xvfb_proc:
            self.xvfb_proc.terminate()
            try:
                self.xvfb_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.xvfb_proc.kill()
        
        if hasattr(self, 'sct'):
            self.sct.close()
