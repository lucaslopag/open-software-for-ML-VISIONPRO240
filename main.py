import sys
from PySide6.QtWidgets import QApplication
from ui import OpenMarsApp

def main():
    app = QApplication(sys.argv)
    
    # Opcional: Icono de la aplicación
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = OpenMarsApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
