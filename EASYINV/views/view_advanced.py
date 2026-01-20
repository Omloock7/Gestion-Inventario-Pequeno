import sys
import os
import shutil
import sqlite3
import zipfile
import json 
import traceback 
import gc   # Necesario para liberar memoria y soltar el archivo
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, 
    QLabel, QFileDialog, QMessageBox, QGroupBox, QTextEdit,
    QDialog, QFormLayout, QDateEdit, QDialogButtonBox 
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtSql import QSqlDatabase 

APP_FOLDER_NAME = "EasyINV" 


if getattr(sys, 'frozen', False):
    # --- MODO EXE (Producción) ---
    BASE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
    # Ruta en AppData (Donde está la DB real)
    USER_DATA_DIR = os.path.join(os.getenv('APPDATA'), APP_FOLDER_NAME)
    
    # Crear carpeta si no existe
    if not os.path.exists(USER_DATA_DIR):
        try:
            os.makedirs(USER_DATA_DIR)
        except OSError:
            USER_DATA_DIR = os.path.join(os.path.expanduser("~"), APP_FOLDER_NAME)
            os.makedirs(USER_DATA_DIR, exist_ok=True)
else:
    # --- MODO DESARROLLO ---
    # Obtenemos la ruta de este archivo (advanced.py)
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    # Si este archivo está dentro de una carpeta "views", subimos un nivel 
    if os.path.basename(current_file_path) == 'views':
        USER_DATA_DIR = os.path.dirname(current_file_path)
    else:
        USER_DATA_DIR = current_file_path

# Definir rutas finales
DB_PATH = os.path.join(USER_DATA_DIR, "inventory.db")
LOG_FILE = os.path.join(USER_DATA_DIR, "error_log.txt")


class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Rango de Fechas")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Fecha Inicio (Por defecto: primer día del mes actual)
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate(QDate.currentDate().year(), QDate.currentDate().month(), 1))
        self.date_start.setDisplayFormat("yyyy-MM-dd")

        # Fecha Fin (Por defecto: hoy)
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setDisplayFormat("yyyy-MM-dd")

        form.addRow("Fecha Inicio:", self.date_start)
        form.addRow("Fecha Fin:", self.date_end)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(btns)

    def get_dates(self):
        # Retorna cadenas de texto YYYY-MM-DD
        return self.date_start.date().toString("yyyy-MM-dd"), self.date_end.date().toString("yyyy-MM-dd")


class AdvancedView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_log_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # TÍTULO
        title = QLabel("Herramientas Avanzadas")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # BASE DE DATOS
        gb_db = QGroupBox("Gestión de Base de Datos")
        layout_db = QVBoxLayout()

        # Mostramos la ruta real para depuración
        lbl_info_db = QLabel(f"Ubicación de datos:\n{DB_PATH}")
        lbl_info_db.setStyleSheet("color: gray; font-size: 10px;")
        lbl_info_db.setWordWrap(True)
        
        btn_export = QPushButton("📦 Crear Copia de Seguridad (.zip)")
        btn_export.clicked.connect(self.export_database)

        btn_import = QPushButton("♻️ Restaurar Copia de Seguridad (.zip)")
        btn_import.clicked.connect(self.import_database)

        layout_db.addWidget(QLabel("Operaciones de respaldo:"))
        layout_db.addWidget(btn_export)
        layout_db.addWidget(btn_import)
        layout_db.addWidget(lbl_info_db)
        gb_db.setLayout(layout_db)
        layout.addWidget(gb_db)

        # REPORTES Y EXPORTACIÓN
        gb_reports = QGroupBox("Reportes y Exportación")
        layout_rep = QVBoxLayout()

        btn_json_sales = QPushButton("📄 Exportar Ventas a JSON")
        btn_json_sales.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        btn_json_sales.clicked.connect(self.export_sales_json)

        layout_rep.addWidget(QLabel("Generar archivos de datos:"))
        layout_rep.addWidget(btn_json_sales)
        gb_reports.setLayout(layout_rep)
        layout.addWidget(gb_reports)

        # LOG DE ERRORES
        gb_log = QGroupBox("Diagnóstico del Sistema")
        layout_log = QVBoxLayout()

        self.txt_log_preview = QTextEdit()
        self.txt_log_preview.setReadOnly(True)
        self.txt_log_preview.setPlaceholderText("Sin errores registrados.")
        self.txt_log_preview.setMaximumHeight(150)

        btn_refresh_log = QPushButton("Actualizar vista de log")
        btn_refresh_log.clicked.connect(self.load_log_preview)
        
        btn_export_log = QPushButton("Guardar archivo de log")
        btn_export_log.clicked.connect(self.export_error_log)

        layout_log.addWidget(QLabel("Registro de fallos:"))
        layout_log.addWidget(btn_refresh_log)
        layout_log.addWidget(self.txt_log_preview)
        layout_log.addWidget(btn_export_log)
        
        gb_log.setLayout(layout_log)
        layout.addWidget(gb_log)

        layout.addStretch()

    # LÓGICA DE EXPORTACIÓN JSON
    def export_sales_json(self):
        # 1. Pedir fechas
        dlg = DateRangeDialog(self)
        if dlg.exec_():
            start_date, end_date = dlg.get_dates()
            
            # Pedir dónde guardar
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Guardar Reporte JSON", 
                f"ventas_detalladas_{start_date}_al_{end_date}.json", 
                "JSON Files (*.json)"
            )
            
            if not filename:
                return

            # Consultar base de datos
            try:   
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Traemos las Ventas
                query_sales = """
                    SELECT * FROM sales 
                    WHERE date(created_at) BETWEEN ? AND ?
                """
                cursor.execute(query_sales, (start_date, end_date))
                sales_rows = cursor.fetchall()
                
                full_sales_data = []

                # Recorremos cada venta para buscar sus PRODUCTOS
                for sale_row in sales_rows:
                    sale_dict = dict(sale_row)
                    sale_id = sale_dict['id']

                    # Buscamos los items de ESTA venta específica
                    query_items = """
                        SELECT item_name, qty, unit_price 
                        FROM sale_items 
                        WHERE sale_id = ?
                    """
                    cursor.execute(query_items, (sale_id,))
                    items_rows = cursor.fetchall()

                    items_list = []
                    for item_row in items_rows:
                        d_item = dict(item_row)
                        # Cálculo simple por seguridad si no existe en BD
                        d_item['subtotal'] = d_item['qty'] * d_item['unit_price']
                        items_list.append(d_item)

                    sale_dict['items_sold'] = items_list
                    full_sales_data.append(sale_dict)

                conn.close()

                # Guardar archivo JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(full_sales_data, f, indent=4, ensure_ascii=False)

                QMessageBox.information(self, "Éxito", f"Se exportaron {len(full_sales_data)} ventas con sus detalles.")

            except Exception as e:
                timestamp_log = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                try:
                    with open(LOG_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"\n[{timestamp_log}] ERROR EN EXPORTACIÓN JSON:\n")
                        f.write(f"Mensaje: {str(e)}\n")
                        traceback.print_exc(file=f)
                        f.write("-" * 50 + "\n")
                except:
                    pass

                QMessageBox.critical(self, "Error", f"Fallo al exportar: {e}\n(Revisa 'Diagnóstico del Sistema')")

    # LÓGICA DE EXPORTACIÓN BD 
    def export_database(self):
        # Usamos un temporal en la misma carpeta USER_DATA para evitar problemas de cruce de discos
        temp_backup_db = os.path.join(USER_DATA_DIR, "temp_backup.db")
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Copia de Seguridad", 
            # CAMBIO SOLICITADO: Solo fecha, sin horas ni minutos
            f"EasyINV_Respaldo_{datetime.now().strftime('%Y%m%d')}.zip", 
            "Zip Files (*.zip)"
        )
        
        if not filename:
            return

        try:
            # Conectamos a la DB REAL (en AppData o Local)
            conn_src = sqlite3.connect(DB_PATH)
            conn_dest = sqlite3.connect(temp_backup_db)
            
            # Usamos la API de backup de SQLite
            conn_src.backup(conn_dest)
            
            conn_dest.close()
            conn_src.close()

            with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Al guardar dentro del zip, le llamamos siempre inventory.db
                zf.write(temp_backup_db, arcname="inventory.db")

            if os.path.exists(temp_backup_db):
                try: os.remove(temp_backup_db)
                except: pass

            QMessageBox.information(self, "Éxito", "Copia de seguridad (.zip) creada correctamente.")

        except Exception as e:
            if os.path.exists(temp_backup_db):
                try: os.remove(temp_backup_db)
                except: pass
            QMessageBox.critical(self, "Error", f"No se pudo crear el respaldo: {str(e)}")

    # LÓGICA DE IMPORTACIÓN BD (MODIFICADA PARA SEGURIDAD)
    def import_database(self):
        confirm = QMessageBox.warning(self, "Peligro", 
                                      "Esta acción REEMPLAZARÁ toda tu base de datos actual.\n"
                                      "Se perderán los datos actuales irremediablemente.\n\n"
                                      "¿Estás seguro de continuar?",
                                      QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No:
            return

        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo de Respaldo", "", "Zip Files (*.zip);;All Files (*)"
        )
        
        if not filename:
            return

        # Rutas auxiliares en AppData
        temp_extract_path = os.path.join(USER_DATA_DIR, "temp_restore_inv.db")
        backup_current_path = os.path.join(USER_DATA_DIR, "inventory.db.bak")

        try:
            # Extraer el zip
            with zipfile.ZipFile(filename, 'r') as zf:
                db_name_in_zip = None
                for name in zf.namelist():
                    if name.endswith(".db"):
                        db_name_in_zip = name
                        break
                
                if not db_name_in_zip:
                    raise ValueError("El archivo ZIP no contiene una base de datos válida (.db)")
                
                with open(temp_extract_path, 'wb') as f_out:
                    f_out.write(zf.read(db_name_in_zip))

            #  CERRAR CONEXIONES DE PYQT
            # Es vital obtener la instancia y removerla antes de tocar el archivo
            db = QSqlDatabase.database()
            connection_name = db.connectionName() 
            
            if db.isOpen():
                db.close()
            
            # Borra la referencia de Python
            del db 
            # Remueve de QtSql
            QSqlDatabase.removeDatabase(connection_name)
            
            # Forzamos limpieza de memoria
            gc.collect()

            # INTERCAMBIO DE ARCHIVOS (SWAP)
            # Primero, si existe la BD actual, la renombramos a .bak (backup de seguridad instantáneo)
            if os.path.exists(DB_PATH):
                # Si ya existía un .bak viejo, lo borramos
                if os.path.exists(backup_current_path):
                    try: os.remove(backup_current_path)
                    except: pass 
                
                try:
                    os.rename(DB_PATH, backup_current_path)
                except OSError:
                    # Si rename falla, intentamos copiar y borrar
                    shutil.move(DB_PATH, backup_current_path)

            # Mover la nueva BD a su lugar
            shutil.move(temp_extract_path, DB_PATH)
            
            QMessageBox.information(self, "Éxito", 
                                    "Base de datos restaurada correctamente.\n"
                                    "La aplicación se cerrará automáticamente para recargar los datos.")
            
            sys.exit()

        except PermissionError:
            # Intento de recuperación si falla por permisos
            if os.path.exists(backup_current_path) and not os.path.exists(DB_PATH):
                try: os.rename(backup_current_path, DB_PATH)
                except: pass

            QMessageBox.critical(self, "Error de Permisos", 
                                 "Windows tiene bloqueado el archivo. Reinicia la PC e intenta de nuevo inmediatamente al abrir la app.")
        
        except Exception as e:
            # Limpieza de temporales
            if os.path.exists(temp_extract_path):
                try: os.remove(temp_extract_path)
                except: pass
            
            # Restaurar backup si existe y la original desapareció
            if os.path.exists(backup_current_path) and not os.path.exists(DB_PATH):
                try: os.rename(backup_current_path, DB_PATH)
                except: pass
            
            # Guardar log
            with open(LOG_FILE, 'a') as f:
                f.write(f"\n[ERROR IMPORT] {str(e)}\n{traceback.format_exc()}")
                
            QMessageBox.critical(self, "Error Fatal", f"Fallo al restaurar: {str(e)}")

    # LÓGICA DE LOGS
    def load_log_preview(self):
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.txt_log_preview.setText(content if content else "Log vacío.")
                    
                    cursor = self.txt_log_preview.textCursor()
                    cursor.movePosition(cursor.End)
                    self.txt_log_preview.setTextCursor(cursor)
            except Exception:
                self.txt_log_preview.setText("No se pudo leer el archivo de log.")
        else:
            self.txt_log_preview.setText("No existe archivo de log.")

    def export_error_log(self):
        if not os.path.exists(LOG_FILE):
            QMessageBox.information(self, "Info", "No hay log para guardar.")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Log", f"log_errores_{datetime.now().strftime('%Y%m%d')}.txt", "Text Files (*.txt)")
        if filename:
            try:
                shutil.copy(LOG_FILE, filename)
                QMessageBox.information(self, "Éxito", "Log guardado.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al guardar: {e}")