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
        
        # Limpiar cualquier rastro de Xvfb zombie
        subprocess.run(["killall", "-9", "Xvfb"], stderr=subprocess.DEVNULL)
        subprocess.run(["rm", "-f", "/tmp/.X99-lock"], stderr=subprocess.DEVNULL)
        subprocess.run(["rm", "-f", "/tmp/.X11-unix/X99"], stderr=subprocess.DEVNULL)
        
        # Iniciar Monitor Fantasma
        print("[WorldBox] Iniciando Xvfb en :99...")
        self.xvfb_proc = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "480x480x24"])
        time.sleep(2) # Esperar a que el servidor X inicie completamente
        
        # Iniciar WorldBox atrapado en :99
        print("[WorldBox] Iniciando binario de Unity sin audio...")
        env = os.environ.copy()
        env["DISPLAY"] = ":99"
        
        # Desactivar Audio forzando drivers nulos/falsos
        env["PULSE_SERVER"] = "dummy"
        env["SDL_AUDIODRIVER"] = "dummy"
        env["ALSO_NONE"] = "1"
        env["FMOD_ALSA_DEVICE"] = "null"
        
        # Forzamos resolución por si acaso
        cmd = [
            "./worldbox/worldbox", 
            "-screen-width", "480", 
            "-screen-height", "480", 
            "-screen-fullscreen", "0"
        ]
        self.wb_proc = subprocess.Popen(cmd, env=env)
        
        # Iniciar Capturador con reintentos
        self.sct = None
        for i in range(5):
            try:
                self.sct = mss.mss(display=":99")
                break
            except Exception as e:
                print(f"[WorldBox] Error conectando a :99, reintentando ({i+1}/5)...")
                time.sleep(1)
                
        if not self.sct:
            print("[WorldBox] FATAL: No se pudo conectar a Xvfb en :99")
            self.running = False
            return
            
        # Iniciar IA Poltergeist
        self.ai_thread = threading.Thread(target=self.ai_loop)
        self.ai_thread.daemon = True
        self.ai_thread.start()

    def xdo(self, *args):
        env = os.environ.copy()
        env["DISPLAY"] = ":99"
        subprocess.run(["xdotool"] + list(args), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def ai_loop(self):
        time.sleep(15) # Esperar a que el juego cargue completamente
        
        # 1. Cerrar Menú de Bienvenida (sin usar Escape para no abrir Ajustes)
        print("[WorldBox AI] Intentando cerrar menú de bienvenida...")
        # Forzar foco en la ventana de X11 haciendo clic en una esquina vacía (arriba)
        self.xdo("mousemove", "240", "10", "click", "1")
        time.sleep(0.5)
        
        # Barrido de seguridad sobre la "X" roja (Arriba a la izquierda del popup)
        # Si el popup no está, solo hará clics inofensivos en el mapa
        for cx in range(75, 125, 10):
            for cy in range(95, 155, 10):
                self.xdo("mousemove", str(cx), str(cy), "click", "1")
                time.sleep(0.05)
                
        # Barrido sobre el botón CERRAR por si acaso
        for cx in range(320, 390, 20):
            self.xdo("mousemove", str(cx), "330", "click", "1")
            time.sleep(0.05)
            
        time.sleep(1.0)
        
        # 2. Hacer Zoom al mínimo (scroll abajo)
        print("[WorldBox AI] Haciendo zoom al mínimo...")
        self.xdo("mousemove", "240", "240")
        for _ in range(20):
            self.xdo("click", "5") # Rueda hacia abajo
            time.sleep(0.1)
        time.sleep(1.0)
        
        # Coordenadas UI estimadas en 480x480
        TABS = {
            'WORLD': (40, 450),
            'NATURE': (120, 450),
            'CIVS': (200, 450),
            'ANIMALS': (280, 450),
            'DISASTERS': (360, 450),
            'DESTRUCT': (440, 450)
        }
        
        # 3. Generar Mapa Nuevo con mucha tierra (Islas) SOLO LA PRIMERA VEZ
        flag_path = os.path.expanduser("~/.config/unity3d/mkarpenko/WorldBox/ai_generated.flag")
        if not os.path.exists(flag_path):
            print("[WorldBox AI] Generando un mapa nuevo gigante (Primera Vez)...")
            self.xdo("mousemove", str(TABS['WORLD'][0]), str(TABS['WORLD'][1]), "click", "1")
            time.sleep(1.0)
            self.xdo("mousemove", "60", "400", "click", "1") # Icono Crear Mundo
            time.sleep(1.5)
            # Seleccionar Preset Continentes o Islas (Centro)
            self.xdo("mousemove", "240", "240", "click", "1") 
            time.sleep(0.5)
            # Seleccionar tamaño Gigante (Centro-Derecha arriba)
            self.xdo("mousemove", "380", "150", "click", "1") 
            time.sleep(0.5)
            # Botón Generar (Abajo centro)
            self.xdo("mousemove", "240", "420", "click", "1") 
            time.sleep(6.0) # Esperar a que acabe de generar
            
            # Guardar flag
            try:
                os.makedirs(os.path.dirname(flag_path), exist_ok=True)
                with open(flag_path, 'w') as f:
                    f.write("done")
            except Exception as e:
                print("No se pudo guardar el flag:", e)
        else:
            print("[WorldBox AI] Mapa ya generado. Cargando partida guardada automáticamente...")
        
        # 4. Iniciar con las poblaciones base (10 Humanos, 10 Orcos)
        print("[WorldBox AI] Spawn de 10 Humanos y 10 Orcos...")
        self.xdo("mousemove", str(TABS['CIVS'][0]), str(TABS['CIVS'][1]), "click", "1")
        time.sleep(1.0)
        
        # Humanos (Izquierda)
        self.xdo("mousemove", "60", "400", "click", "1")
        time.sleep(0.5)
        for _ in range(15):
            self.xdo("mousemove", str(random.randint(50, 200)), str(random.randint(100, 350)), "click", "1")
            time.sleep(0.1)
            
        # Orcos (Derecha)
        self.xdo("mousemove", "180", "400", "click", "1")
        time.sleep(0.5)
        for _ in range(15):
            self.xdo("mousemove", str(random.randint(280, 430)), str(random.randint(100, 350)), "click", "1")
            time.sleep(0.1)
            
        last_resource_time = time.time()
        last_disaster_time = time.time()
        
        resource_interval = random.randint(600, 1800) # 10 a 30 mins
        disaster_interval = random.randint(300, 900)  # 5 a 15 mins
        
        while self.running:
            now = time.time()
            
            # Evento: Recursos
            if now - last_resource_time > resource_interval:
                print("[WorldBox AI] Evento: Lluvia de Recursos!")
                self.xdo("mousemove", str(TABS['NATURE'][0]), str(TABS['NATURE'][1]), "click", "1")
                time.sleep(1.0)
                # Seleccionar un recurso mineral (Oro, Hierro, Piedra)
                self.xdo("mousemove", str(random.choice([150, 200, 250])), "400", "click", "1")
                time.sleep(0.5)
                
                # Dropear recursos
                for _ in range(30):
                    self.xdo("mousemove", str(random.randint(50, 430)), str(random.randint(50, 350)), "click", "1")
                    time.sleep(0.1)
                    
                last_resource_time = now
                resource_interval = random.randint(600, 1800)
                
            # Evento: Desastre Menor
            if now - last_disaster_time > disaster_interval:
                print("[WorldBox AI] Evento: Desastre Aleatorio!")
                self.xdo("mousemove", str(TABS['DISASTERS'][0]), str(TABS['DISASTERS'][1]), "click", "1")
                time.sleep(1.0)
                
                # Seleccionar Meteorito o Terremoto
                # (Evitamos la Tsar Bomba o Antimateria que están a la derecha)
                safe_disasters_x = [60, 120, 180] 
                self.xdo("mousemove", str(random.choice(safe_disasters_x)), "400", "click", "1")
                time.sleep(0.5)
                
                # Tirar 1 o 2 desastres
                for _ in range(random.randint(1, 2)):
                    self.xdo("mousemove", str(random.randint(100, 380)), str(random.randint(100, 250)), "click", "1")
                    time.sleep(0.3)
                    
                last_disaster_time = now
                disaster_interval = random.randint(300, 900)
                
            # Comportamiento Pasivo (Mover la cámara y mirar)
            self.xdo("mousemove", "240", "240", "mousedown", "3") # Clic derecho
            self.xdo("mousemove_relative", "--", str(random.randint(-150, 150)), str(random.randint(-150, 150)))
            self.xdo("mouseup", "3")
            time.sleep(random.uniform(5.0, 10.0))

    def get_frame(self):
        if not self.running or not getattr(self, 'sct', None):
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
