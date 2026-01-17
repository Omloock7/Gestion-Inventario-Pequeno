import sys
import os
import traceback
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

# Revisa la ruta donde está main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "error_log.txt")

#Se ejecuta automáticamente cuando ocurre un error no controlado.
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Obtener fecha y mensaje
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # Imprimir en consola
    print("¡ERROR CAPTURADO POR EL LOGGER!", file=sys.stderr)
    print(error_msg)

    # Guardar en archivo
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}] ERROR NO CONTROLADO:\n")
            f.write(error_msg)
            f.write("-" * 80 + "\n")
    except Exception as e:
        print(f"No se pudo escribir el log: {e}")

def setup_error_logging():
    # Conecta la función a las excepciones de python
    sys.excepthook = handle_exception