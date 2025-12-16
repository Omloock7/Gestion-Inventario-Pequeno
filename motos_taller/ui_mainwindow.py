# ui_mainwindow.py - ventana principal integrada con los diálogos
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
    QMessageBox, QDialog, QTextEdit, QHeaderView # <-- ¡AÑADIDOS!
)
from PyQt5.QtCore import Qt
import db, textwrap

# importa tus diálogos (asegúrate de que los nombres de las clases coincidan)
from dialogs.dlg_add_item import AddItemDialog
from dialogs.dlg_delete_item import DeleteItemDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taller de Motos - Inventario y Ventas")
        self.resize(900, 600)
        db.init_db()  # asegurar DB creada
        self._setup_ui()
        self.load_items()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        v = QVBoxLayout()
        central.setLayout(v)

        # Barra superior simple: búsqueda y botones
        top = QHBoxLayout()
        v.addLayout(top)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o SKU...")
        self.search_input.returnPressed.connect(self.on_search)
        top.addWidget(self.search_input)

        btn_refresh = QPushButton("Refrescar")
        btn_refresh.clicked.connect(self.load_items)
        top.addWidget(btn_refresh)

        # botón para abrir diálogo de añadir (usa tu dlg_add_item)
        btn_add = QPushButton("Añadir item")
        btn_add.clicked.connect(self.open_add_item_dialog)
        top.addWidget(btn_add)

        # botón para eliminar (abre dlg_delete_item)
        btn_delete = QPushButton("Eliminar item")
        btn_delete.clicked.connect(self.open_delete_item_dialog)
        top.addWidget(btn_delete)

        btn_sales = QPushButton("Ventas (abrir)")
        btn_sales.clicked.connect(self.on_open_sales)
        top.addWidget(btn_sales)

        # Tabla de items
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "SKU", "Nombre", "Precio", "Stock", "Proveedor"])
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        v.addWidget(self.table)

        # Pie
        bottom = QHBoxLayout()
        v.addLayout(bottom)
        self.status_label = QLabel("Listo")
        bottom.addWidget(self.status_label)
        bottom.addStretch()

        # permitir doble clic para editar/seleccionar fila (opcional)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)

    def load_items(self):
        items = db.get_items(500)
        self.table.setRowCount(0)
        for it in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(it["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(it.get("sku") or ""))
            self.table.setItem(row, 2, QTableWidgetItem(it.get("name") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(f'{it.get("price",0):.2f}'))
            self.table.setItem(row, 4, QTableWidgetItem(str(it.get("stock",0))))
            self.table.setItem(row, 5, QTableWidgetItem(str(it.get("provider_id") or "")))
        self.status_label.setText(f"{len(items)} items cargados")

    def on_search(self):
        text = self.search_input.text().strip().lower()
        if not text:
            self.load_items()
            return
        items = db.get_items(500)
        filtered = [it for it in items if text in (it.get("name") or "").lower() or text in (it.get("sku") or "").lower()]
        self.table.setRowCount(0)
        for it in filtered:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(it["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(it.get("sku") or ""))
            self.table.setItem(row, 2, QTableWidgetItem(it.get("name") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(f'{it.get("price",0):.2f}'))
            self.table.setItem(row, 4, QTableWidgetItem(str(it.get("stock",0))))
            self.table.setItem(row, 5, QTableWidgetItem(str(it.get("provider_id") or "")))
        self.status_label.setText(f"{len(filtered)} resultados")

    # abrir diálogo para agregar item y guardarlo en la DB
    def open_add_item_dialog(self):
        dialog = AddItemDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_data()
            except Exception as e:
                QMessageBox.warning(self, "Datos inválidos", f"Revisa los campos: {e}")
                return

            # validaciones básicas
            if not data.get("name"):
                QMessageBox.warning(self, "Nombre requerido", "El campo Nombre es obligatorio.")
                return

            # evitar duplicar SKU
            if data.get("sku"):
                exists = db.get_item_by_sku(data["sku"])
                if exists:
                    QMessageBox.warning(self, "SKU duplicado", "Ya existe un ítem con ese SKU.")
                    return

            try:
                db.add_item(
                    sku=data.get("sku"),
                    name=data.get("name"),
                    description=data.get("description"),
                    price=float(data.get("price") or 0.0),
                    stock=int(data.get("stock") or 0)
                )
                self.load_items()
                QMessageBox.information(self, "OK", "Ítem agregado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error al guardar", str(e))

    # abrir diálogo para eliminar item por SKU
    def open_delete_item_dialog(self):
        dialog = DeleteItemDialog(self)
        if dialog.exec_():
            sku = dialog.get_sku()
            if not sku:
                QMessageBox.warning(self, "SKU vacío", "Proporciona el SKU del ítem a eliminar.")
                return
            # Confirmación
            r = QMessageBox.question(self, "Confirmar", f"¿Eliminar el ítem con SKU '{sku}'?", QMessageBox.Yes | QMessageBox.No)
            if r != QMessageBox.Yes:
                return
            try:
                rows = db.delete_item_by_sku(sku)
                if rows:
                    QMessageBox.information(self, "Eliminado", "Ítem eliminado correctamente.")
                    self.load_items()
                else:
                    QMessageBox.warning(self, "No encontrado", "No existe ningún ítem con ese SKU.")
            except Exception as e:
                QMessageBox.critical(self, "Error al eliminar", str(e))

    def on_open_sales(self):
        QMessageBox.information(self, "Ventas", "Ventana de ventas aún no implementada. Próximo paso.")

    def on_table_double_click(self, row, col):
        """
        Muestra la información detallada del ítem seleccionado 
        al hacer doble clic en una fila de la tabla.
        """
        # 1. Obtener el ID del ítem de la primera columna (col=0)
        try:
            item_id = self.table.item(row, 0).text()
        except AttributeError:
            # Maneja el caso en que la celda esté vacía o no sea QTableWidgetItem
            return 

        # 2. Obtener los datos completos del ítem desde la base de datos
        item = db.get_item_by_id(item_id)
        
        if item:
            MAX_WIDTH = 60  # Límite de caracteres por línea

            # Obtener y formatear la descripción para evitar que el MessageBox se extienda
            description = item.get('description', 'N/A')
            wrapped_description = textwrap.fill(description, MAX_WIDTH)

            # 3. Construir el mensaje
            message = (
                f"ID: {item['id']}\n"
                f"SKU: {item.get('sku', 'N/A')}\n"
                f"-------------------\n"
                f"Nombre: {item.get('name', 'N/A')}\n"
                f"Stock: {item.get('stock', 'N/A')}\n"
                f"Precio: {item.get('price', 0.0):.2f}\n"
                f"--- Descripción ---\n"
                f"{wrapped_description}"
            )

            # 4. Mostrar el diálogo de información
            QMessageBox.information(
                self, 
                "Detalle Ítem", 
                message
            )