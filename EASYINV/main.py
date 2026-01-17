import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon 
from ui_mainwindow import MainWindow 
import db
import logger_config

# --- FUNCIÓN CORREGIDA PARA RUTAS ---
def resource_path(relative_path):
    """ 
    Obtiene la ruta absoluta al recurso. 
    Funciona tanto en el .exe (PyInstaller) como en desarrollo.
    """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # MODO DESARROLLO (CORREGIDO):
        # Usamos la ubicación exacta de ESTE archivo main.py
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def main():
    # 1. Configuración de Logs
    logger_config.setup_error_logging()
    
    # 2. Inicialización de DB
    # La DB se creará donde esté el archivo .exe (o el .py), no en temporales
    print("Iniciando sistema...")
    db.init_db()
    print("Base de datos conectada correctamente.")
     
    # 3. Configuración para barra de tareas Windows (AppID)
    # Esto evita que el icono se pierda en la barra de tareas de Windows
    try:
        myappid = 'miempresa.easyinv.sistema.v1' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass 

    app = QApplication(sys.argv)
    
    # 4. Cargar el icono usando la función segura
    # Esto busca "assets/logo.ico" correctamente ahora
    logo_path = resource_path(os.path.join("assets", "logo.ico"))

    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))
    else:
        # Debug: Imprime dónde está buscando si falla
        print(f"Advertencia CRÍTICA: No se encontró el logo en: {logo_path}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()