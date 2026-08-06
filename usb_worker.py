import time
import usb.core
from PySide6.QtCore import QThread, Signal
from init_cmds import INIT_COMMANDS

VID, PID = 0x345F, 0x9132

class UsbWorker(QThread):
    """
    Hilo en segundo plano dedicado exclusivamente a la comunicación USB con el MS9132.
    Lee el payload activo y lo escupe a 30 FPS manteniendo el heartbeat.
    """
    status_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.dev = None
        self.active_payload = None

    def conectar(self):
        self.dev = usb.core.find(idVendor=VID, idProduct=PID)
        if not self.dev:
            self.status_changed.emit("Desconectado (Pantalla no encontrada o falta permisos)")
            return False
        try:
            if self.dev.is_kernel_driver_active(0): 
                self.dev.detach_kernel_driver(0)
        except Exception: pass
        try:
            # Evitar Errno 16 Resource Busy si ya está configurado
            cfg = self.dev.get_active_configuration()
            if cfg is None:
                self.dev.set_configuration()
        except Exception: pass
        return True

    def inicializar(self):
        self.status_changed.emit("Inicializando pantalla...")
        for f in INIT_COMMANDS:
            try:
                self.dev.ctrl_transfer(
                    f['bmRequestType'], f['bRequest'], f['wValue'], 
                    f['wIndex'], f['data_or_len'], timeout=100
                )
            except Exception: pass
            time.sleep(0.005)
        
        self.status_changed.emit("Despertando panel LCD...")
        time.sleep(1.0)
        self.heartbeat()

    def heartbeat(self):
        for bm, br, d in [
            (0x21, 0x09, bytes.fromhex('b500320000000000')),
            (0xa1, 0x01, 8),
            (0x21, 0x09, bytes.fromhex('b500320000000000')),
            (0xa1, 0x01, 8)
        ]:
            try: self.dev.ctrl_transfer(bm, br, 0x0300, 0, d, timeout=100)
            except Exception: pass

    def update_payload(self, payload):
        """Thread-safe update of the current frame to display"""
        self.active_payload = payload

    def get_black_payload(self):
        # Cachear payload negro para evitar recalcular
        if not hasattr(self, '_black_payload'):
            CABECERA = b'\xff\x00\x00\x00\x00\x1e\x01\xe0'
            PIE      = b'\xff\xc0\x00\x00\x00\x00\x00\x00'
            # 480x480x3 bytes de negro (0x00)
            pixeles = bytes(480 * 480 * 3)
            self._black_payload = CABECERA + pixeles + PIE
        return self._black_payload

    def run(self):
        self.running = True
        if not self.conectar():
            self.running = False
            return
            
        self.inicializar()
        self.status_changed.emit("Conectado y Reproduciendo")
        
        while self.running:
            start_time = time.time()
            
            payload = self.active_payload if self.active_payload else self.get_black_payload()
            try:
                self.dev.write(0x04, payload, timeout=2000)
                self.heartbeat()
            except Exception as e:
                self.status_changed.emit(f"Error USB: {e}")
                time.sleep(1)
                if self.conectar():
                    self.inicializar()
                    self.status_changed.emit("Conectado y Reproduciendo")
                    
            elapsed = time.time() - start_time
            sleep_time = 0.033 - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self):
        self.running = False
        self.wait()
