import sys, os, shutil, sqlite3, zipfile, traceback, gc
import csv, codecs, json
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
    USER_DATA_DIR = os.path.join(os.getenv('APPDATA'), APP_FOLDER_NAME)
    if not os.path.exists(USER_DATA_DIR):
        try:
            os.makedirs(USER_DATA_DIR)
        except OSError:
            USER_DATA_DIR = os.path.join(os.path.expanduser("~"), APP_FOLDER_NAME)
            os.makedirs(USER_DATA_DIR, exist_ok=True)
else:
    # --- MODO DESARROLLO ---
    current_file_path = os.path.dirname(os.path.abspath(__file__))
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

        # IMPORTACIÓN MASIVA
        gb_import = QGroupBox("Importación Masiva de Inventario (Excel/CSV)")
        gb_import.setStyleSheet("QGroupBox { font-weight: bold; color: #27ae60; border: 1px solid #27ae60; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        layout_imp = QVBoxLayout()

        lbl_instr = QLabel("Instrucciones: Descarga la plantilla, llénala en Excel y guárdala como 'CSV UTF-8'.")
        lbl_instr.setStyleSheet("color: #555; font-size: 11px; font-weight: normal;")
        
        # Botones
        btn_template = QPushButton("⬇️ Descargar Plantilla Excel (.csv)")
        btn_template.clicked.connect(self.download_csv_template)
        
        btn_upload = QPushButton("⬆️ Subir Archivo CSV")
        btn_upload.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_upload.clicked.connect(self.import_products_csv)

        layout_imp.addWidget(lbl_instr)
        layout_imp.addWidget(btn_template)
        layout_imp.addWidget(btn_upload)
        gb_import.setLayout(layout_imp)
        layout.addWidget(gb_import)

        # BASE DE DATOS
        gb_db = QGroupBox("Gestión de Base de Datos")
        layout_db = QVBoxLayout()

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

        btn_low_stock = QPushButton("⚠️ Generar Reporte de Pedidos (Excel)")
        btn_low_stock.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        btn_low_stock.clicked.connect(self.export_order_report)

        layout_rep.addWidget(QLabel("Generar archivos de datos:"))
        layout_rep.addWidget(btn_json_sales)
        layout_rep.addWidget(btn_low_stock)
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


    # LOGICA IMPORTACIÓN CSV 
    def download_csv_template(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Plantilla", "plantilla_productos.csv", "CSV Files (*.csv)"
        )
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';')
                    headers = [
                        "SKU (Obligatorio)", 
                        "Nombre (Obligatorio)", 
                        "Proveedor", 
                        "Telefono Proveedor", 
                        "Ubicacion", 
                        "Descripcion", 
                        "Precio Publico", 
                        "Precio Mayorista", 
                        "Precio Distribuidor", 
                        "Stock Actual", 
                        "Stock Minimo", 
                        "Stock Maximo"
                    ]
                    writer.writerow(headers)
                    writer.writerow([
                        "USB-001", "Memoria USB Ejemplo", "Kingston", "3001234567", "Caja 1", 
                        "Descripcion del producto...", "15.50", "12.00", "10.00", "100", "5", "500"
                    ])
                QMessageBox.information(self, "Éxito", "Plantilla guardada. Ábrela con Excel.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    def import_products_csv(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar CSV", "", "CSV Files (*.csv);;Text Files (*.txt)"
        )
        if not filename:
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            rows_inserted = 0
            providers_created = 0 
            errors = []

            with open(filename, 'r', encoding='utf-8-sig', errors='replace') as f:
                sample = f.read(1024)
                f.seek(0)
                delimiter = ';' if ';' in sample else ','
                
                reader = csv.reader(f, delimiter=delimiter)
                header = next(reader, None)

                if not header:
                    raise ValueError("El archivo está vacío")

                for row_idx, row in enumerate(reader, start=2):
                    if len(row) < 2: continue
                    
                    try:
                        sku = row[0].strip()
                        if not sku: continue
                        
                        name = row[1].strip()
                        provider_name = row[2].strip() if len(row) > 2 else ""
                        provider_phone = row[3].strip() if len(row) > 3 else "" 
                        location = row[4].strip() if len(row) > 4 else ""
                        desc = row[5].strip() if len(row) > 5 else ""
                        
                        # Helpers numéricos
                        def p_float(v):
                            if not v: return 0.0
                            return float(v.replace(',', '.').replace('$', '').strip())
                        
                        def p_int(v, d=0):
                            if not v: return d
                            try: return int(float(v))
                            except: return d

                        price_pub = p_float(row[6]) if len(row) > 6 else 0.0
                        price_may = p_float(row[7]) if len(row) > 7 else 0.0  # price_c1
                        price_dis = p_float(row[8]) if len(row) > 8 else 0.0  # price_c2
                        
                        stock = p_int(row[9] if len(row) > 9 else "0")
                        min_s = p_int(row[10] if len(row) > 10 else "1", 1)
                        max_s = p_int(row[11] if len(row) > 11 else "100", 100)

                        #  LÓGICA DE PROVEEDOR 
                        final_provider_id = None
                        
                        if provider_name:
                            #  Buscamos ID
                            cursor.execute("SELECT id FROM providers WHERE name = ?", (provider_name,))
                            row_prov = cursor.fetchone()
                            
                            if row_prov:
                                final_provider_id = row_prov[0]
                            else:
                                #  Crear si no existe
                                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                cursor.execute("""
                                    INSERT INTO providers (name, phone, created_at, active) 
                                    VALUES (?, ?, ?, 1)
                                """, (provider_name, provider_phone, now_str))
                                final_provider_id = cursor.lastrowid
                                providers_created += 1

                        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # INSERTAR EN TABLA 'ITEMS'
                        query = """
                            INSERT INTO items (
                                sku, name, provider_id, location, description, 
                                price, price_c1, price_c2, 
                                stock, min_stock, max_stock, created_at, active
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                            ON CONFLICT(sku) DO UPDATE SET
                                name=excluded.name,
                                provider_id=excluded.provider_id,
                                price=excluded.price,
                                price_c1=excluded.price_c1,
                                price_c2=excluded.price_c2,
                                stock=stock + excluded.stock 
                        """
                        
                        cursor.execute(query, (
                            sku, name, final_provider_id, location, desc, 
                            price_pub, price_may, price_dis, 
                            stock, min_s, max_s, created_at
                        ))
                        rows_inserted += 1

                    except Exception as row_e:
                        errors.append(f"Fila {row_idx}: {str(row_e)}")

            conn.commit()
            conn.close()

            msg = f"Importación finalizada.\n\n" \
                  f"📦 Productos procesados: {rows_inserted}\n" \
                  f"🏢 Nuevos proveedores creados: {providers_created}"
            
            if errors:
                msg += f"\n\nErrores ({len(errors)}):\n" + "\n".join(errors[:5])
            
            QMessageBox.information(self, "Importación Completa", msg)

        except Exception as e:
            if conn: conn.close()
            with open(LOG_FILE, 'a') as f:
                f.write(f"\n[IMPORT CSV ERROR] {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error Fatal", f"No se pudo importar: {e}")

    # LÓGICA DE EXPORTACIÓN PEDIDOS
    def export_order_report(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Reporte de Pedidos", 
            f"Pedido_Sugerido_{datetime.now().strftime('%Y-%m-%d')}.csv", 
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            query = """
                SELECT 
                    p.name,             
                    p.phone,            
                    i.sku,              
                    i.name,             
                    i.stock,            
                    i.min_stock,        
                    i.max_stock,        
                    (i.max_stock - i.stock) as qty_needed 
                FROM items i
                LEFT JOIN providers p ON i.provider_id = p.id
                WHERE i.stock <= i.min_stock
                ORDER BY p.name ASC, i.name ASC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                QMessageBox.information(self, "Todo en orden", "No hay productos con stock bajo en este momento.")
                conn.close()
                return

            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                headers = [
                    "Proveedor", "Teléfono Contacto", "SKU", "Producto", 
                    "Stock Actual", "Stock Mínimo", "Stock Máximo", 
                    "CANTIDAD A PEDIR (Sugerida)"
                ]
                writer.writerow(headers)

                for row in rows:
                    prov_name = row[0] if row[0] else "--- Sin Asignar ---"
                    prov_phone = row[1] if row[1] else ""
                    qty_needed = row[7]
                    if qty_needed < 0: qty_needed = 0

                    writer.writerow([
                        prov_name, prov_phone, row[2], row[3], 
                        row[4], row[5], row[6], qty_needed
                    ])

            conn.close()
            QMessageBox.information(self, "Reporte Generado", f"Se ha generado la lista de pedidos con {len(rows)} productos.")

        except Exception as e:
            if conn: conn.close()
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte: {e}")

    # LÓGICA DE EXPORTACIÓN JSON
    def export_sales_json(self):
        dlg = DateRangeDialog(self)
        if dlg.exec_():
            start_date, end_date = dlg.get_dates()
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Guardar Reporte JSON", 
                f"ventas_detalladas_{start_date}_al_{end_date}.json", 
                "JSON Files (*.json)"
            )
            
            if not filename:
                return

            try:   
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query_sales = """
                    SELECT * FROM sales 
                    WHERE date(created_at) BETWEEN ? AND ?
                """
                cursor.execute(query_sales, (start_date, end_date))
                sales_rows = cursor.fetchall()
                
                full_sales_data = []

                for sale_row in sales_rows:
                    sale_dict = dict(sale_row)
                    sale_id = sale_dict['id']

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
                        d_item['subtotal'] = d_item['qty'] * d_item['unit_price']
                        items_list.append(d_item)

                    sale_dict['items_sold'] = items_list
                    full_sales_data.append(sale_dict)

                conn.close()

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

    # LÓGICA DE EXPORTACIÓN BD (BACKUP ZIP)
    def export_database(self):
        temp_backup_db = os.path.join(USER_DATA_DIR, "temp_backup.db")
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Copia de Seguridad", 
            f"EasyINV_Respaldo_{datetime.now().strftime('%Y%m%d')}.zip", 
            "Zip Files (*.zip)"
        )
        
        if not filename:
            return

        try:
            conn_src = sqlite3.connect(DB_PATH)
            conn_dest = sqlite3.connect(temp_backup_db)
            conn_src.backup(conn_dest)
            conn_dest.close()
            conn_src.close()

            with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
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

    # LÓGICA DE IMPORTACIÓN BD
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

        temp_extract_path = os.path.join(USER_DATA_DIR, "temp_restore_inv.db")
        backup_current_path = os.path.join(USER_DATA_DIR, "inventory.db.bak")

        try:
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

            #  CERRAR CONEXIONES
            db = QSqlDatabase.database()
            connection_name = db.connectionName() 
            if db.isOpen():
                db.close()
            del db 
            QSqlDatabase.removeDatabase(connection_name)
            gc.collect()

            # SWAP
            if os.path.exists(DB_PATH):
                if os.path.exists(backup_current_path):
                    try: os.remove(backup_current_path)
                    except: pass 
                try:
                    os.rename(DB_PATH, backup_current_path)
                except OSError:
                    shutil.move(DB_PATH, backup_current_path)

            shutil.move(temp_extract_path, DB_PATH)
            
            QMessageBox.information(self, "Éxito", 
                                    "Base de datos restaurada correctamente.\n"
                                    "La aplicación se cerrará automáticamente para recargar los datos.")
            sys.exit()

        except PermissionError:
            if os.path.exists(backup_current_path) and not os.path.exists(DB_PATH):
                try: os.rename(backup_current_path, DB_PATH)
                except: pass
            QMessageBox.critical(self, "Error de Permisos", 
                                 "Windows tiene bloqueado el archivo. Reinicia la PC e intenta de nuevo.")
        
        except Exception as e:
            if os.path.exists(temp_extract_path):
                try: os.remove(temp_extract_path)
                except: pass
            if os.path.exists(backup_current_path) and not os.path.exists(DB_PATH):
                try: os.rename(backup_current_path, DB_PATH)
                except: pass
            
            with open(LOG_FILE, 'a') as f:
                f.write(f"\n[ERROR IMPORT] {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error Fatal", f"Fallo al restaurar: {str(e)}")

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
                
                