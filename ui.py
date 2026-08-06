import os
import json
import shutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QListWidget, QListWidgetItem, QComboBox,
    QGroupBox, QFormLayout, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap

from usb_worker import UsbWorker
from media_worker import MediaWorker

class OpenMarsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Open Screen for Mars Gaming")
        self.setMinimumSize(900, 600)
        
        # Tema Oscuro Básico
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #0d47a1;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QListWidget {
                background-color: #252526;
                border: 1px solid #333;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
            }
            QGroupBox {
                border: 1px solid #333;
                border-radius: 4px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #aaa;
            }
            QComboBox {
                background-color: #333;
                border: 1px solid #555;
                padding: 4px;
                border-radius: 4px;
            }
        """)

        # Workers
        self.usb_worker = UsbWorker()
        self.media_worker = MediaWorker(self.usb_worker)
        
        # Conectar Señales
        self.usb_worker.status_changed.connect(self.update_status)
        self.media_worker.preview_ready.connect(self.update_preview)

        # UI Setup
        self.setup_ui()
        
        # Cargar configuración previa
        self.load_config()
        
        # Iniciar Hilos
        self.usb_worker.start()
        self.media_worker.start()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # PANEL IZQUIERDO: Directorio y Galería
        left_panel = QVBoxLayout()
        
        btn_folder = QPushButton("📁 Abrir Directorio de Medios")
        btn_folder.clicked.connect(self.open_directory)
        left_panel.addWidget(btn_folder)

        obs_layout = QHBoxLayout()
        btn_camera = QPushButton("🎥 Conectar a OBS Virtual Camera")
        btn_camera.setStyleSheet("background-color: #d32f2f;") # Rojo para destacar
        btn_camera.clicked.connect(self.on_camera_selected)
        
        btn_info = QPushButton("ℹ️")
        btn_info.setStyleSheet("background-color: #555; font-size: 16px; padding: 4px;")
        btn_info.setFixedWidth(40)
        btn_info.clicked.connect(self.show_obs_info)
        
        obs_layout.addWidget(btn_camera)
        obs_layout.addWidget(btn_info)
        left_panel.addLayout(obs_layout)
        
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListWidget.IconMode)
        self.gallery.setIconSize(QSize(100, 100))
        self.gallery.setResizeMode(QListWidget.Adjust)
        self.gallery.setSpacing(10)
        self.gallery.itemClicked.connect(self.on_media_selected)
        left_panel.addWidget(self.gallery)
        
        # PANEL DERECHO: Previsualización y Controles
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignTop)
        
        # Previsualización
        self.lbl_preview = QLabel("Esperando Imagen...")
        self.lbl_preview.setFixedSize(480, 480)
        self.lbl_preview.setStyleSheet("background-color: #000; border: 2px solid #333; border-radius: 8px;")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        right_panel.addWidget(self.lbl_preview)
        
        # Controles
        group_controls = QGroupBox("Ajustes de Pantalla")
        form = QFormLayout(group_controls)
        
        self.cb_rotation = QComboBox()
        self.cb_rotation.addItems(["0º", "90º", "180º", "270º"])
        self.cb_rotation.currentIndexChanged.connect(self.update_transform)
        
        self.cb_scale = QComboBox()
        self.cb_scale.addItems(["Recortar (Mantener Proporción)", "Aplastar (Estirar a 480x480)"])
        self.cb_scale.currentIndexChanged.connect(self.update_transform)
        
        self.chk_autostart = QCheckBox("Iniciar automáticamente con el PC")
        self.chk_autostart.stateChanged.connect(self.toggle_autostart)
        
        form.addRow("Rotación:", self.cb_rotation)
        form.addRow("Modo Escala:", self.cb_scale)
        form.addRow("", self.chk_autostart)
        right_panel.addWidget(group_controls)
        
        # Estado
        self.lbl_status = QLabel("Desconectado")
        self.lbl_status.setStyleSheet("color: #ff5252; font-weight: bold; padding-top: 10px;")
        right_panel.addWidget(self.lbl_status)
        
        # Layout principal
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=0)

    def update_transform(self):
        rot_str = self.cb_rotation.currentText().replace("º", "")
        rotation = int(rot_str) if rot_str.isdigit() else 0
        
        scale_mode = "fit" if self.cb_scale.currentIndex() == 0 else "stretch"
        self.media_worker.set_transform(rotation, scale_mode)

    def open_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if folder:
            self.gallery.clear()
            valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.mp4', '.avi', '.mkv', '.webm')
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(valid_exts):
                    path = os.path.join(folder, f)
                    item = QListWidgetItem(f)
                    item.setData(Qt.UserRole, path)
                    
                    # Intentar crear un icono de previsualización rápido para la galería
                    if not f.lower().endswith(('.mp4', '.avi', '.mkv', '.webm')):
                        try:
                            pixmap = QPixmap(path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setIcon(QIcon(pixmap))
                        except: pass
                    
                    self.gallery.addItem(item)

    def show_obs_info(self):
        QMessageBox.information(self, "Cómo usar la Cámara Virtual",
            "La integración con OBS Studio te permite usar la pantalla LCD como un monitor secundario "
            "o mostrar widgets avanzados (temperaturas, navegadores web, juegos) saltándote las "
            "restricciones de seguridad de Linux/Wayland.\n\n"
            "Instrucciones:\n"
            "1. Abre OBS Studio en tu ordenador.\n"
            "2. En 'Fuentes', añade lo que quieras mostrar en la pantalla (p. ej., 'Captura de pantalla (PipeWire)', 'Captura de Ventana', etc.).\n"
            "3. En los controles de OBS, haz clic en el botón 'Iniciar Cámara Virtual'.\n"
            "4. Vuelve aquí y haz clic en el botón rojo 'Conectar a OBS Virtual Camera'.\n\n"
            "La pantalla mostrará instantáneamente tu OBS a 30 FPS. Si ves la imagen distorsionada, asegúrate "
            "de que la resolución de salida en los ajustes de OBS sea cuadrada (ej. 480x480 o 1080x1080)."
        )

    def on_camera_selected(self):
        self.gallery.clearSelection()
        self.media_worker.load_media('OBS_CAMERA')

    def on_media_selected(self, item):
        path = item.data(Qt.UserRole)
        self.media_worker.load_media(path)

    def update_preview(self, qimage):
        pixmap = QPixmap.fromImage(qimage)
        self.lbl_preview.setPixmap(pixmap)

    def update_status(self, text):
        self.lbl_status.setText(text)
        if "Error" in text or "Desconectado" in text:
            self.lbl_status.setStyleSheet("color: #ff5252; font-weight: bold; padding-top: 10px;")
        else:
            self.lbl_status.setStyleSheet("color: #4caf50; font-weight: bold; padding-top: 10px;")

    def closeEvent(self, event):
        self.save_config()
        self.usb_worker.stop()
        self.media_worker.stop()
        event.accept()

    def get_autostart_path(self):
        return os.path.expanduser("~/.config/autostart/open-screen-mars.desktop")

    def toggle_autostart(self, state):
        autostart_file = self.get_autostart_path()
        if state == Qt.Checked.value:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(autostart_file), exist_ok=True)
            
            # Generar contenido del .desktop
            app_dir = os.path.dirname(os.path.abspath(__file__))
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Open Screen for Mars Gaming
Comment=Controlador nativo para pantallas LCD Mars Gaming (MS9132)
Exec={app_dir}/run.sh
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;HardwareSettings;
"""
            with open(autostart_file, 'w') as f:
                f.write(desktop_content)
            os.chmod(autostart_file, 0o755)
        else:
            if os.path.exists(autostart_file):
                os.remove(autostart_file)

    def save_config(self):
        config = {
            'rotation': self.cb_rotation.currentIndex(),
            'scale': self.cb_scale.currentIndex(),
            'autostart': self.chk_autostart.isChecked(),
            'last_media': self.media_worker.media_path
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    
                self.cb_rotation.setCurrentIndex(config.get('rotation', 0))
                self.cb_scale.setCurrentIndex(config.get('scale', 0))
                
                autostart = config.get('autostart', False)
                self.chk_autostart.setChecked(autostart)
                # Verificar sincronización con el sistema real
                if autostart and not os.path.exists(self.get_autostart_path()):
                    self.toggle_autostart(Qt.Checked.value)
                
                last_media = config.get('last_media', None)
                if last_media:
                    self.media_worker.load_media(last_media)
            except Exception as e:
                print(f"Error cargando config: {e}")
