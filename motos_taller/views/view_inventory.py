# views/view_inventory.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QMessageBox
)
import db
from dialogs.dlg_add_item import AddItemDialog
from dialogs.dlg_item_detail import ItemDetailDialog  # Importamos desde la nueva ubicación

class InventoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_items()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Barra Superior ---
        top_bar = QHBoxLayout()
        layout.addLayout(top_bar)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o SKU...")
        self.search_input.returnPressed.connect(self.on_search)
        top_bar.addWidget(self.search_input)

        btn_refresh = QPushButton("Refrescar")
        btn_refresh.clicked.connect(self.load_items)
        top_bar.addWidget(btn_refresh)

        btn_add = QPushButton("Añadir item")
        btn_add.clicked.connect(self.open_add_item_dialog)
        top_bar.addWidget(btn_add)

        btn_delete = QPushButton("Eliminar item")
        btn_delete.clicked.connect(self.open_delete_item_dialog)
        top_bar.addWidget(btn_delete)
        
        # --- Tabla ---
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "SKU", "Nombre", "Precio", "Stock", "Proveedor"])
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)
        layout.addWidget(self.table)

        # --- Pie ---
        bottom_bar = QHBoxLayout()
        layout.addLayout(bottom_bar)
        self.status_label = QLabel("Listo")
        bottom_bar.addWidget(self.status_label)
        bottom_bar.addStretch()

    # --- LÓGICA DEL INVENTARIO ---

    def load_items(self):
        items = db.get_items(500)
        self.update_table(items)
        self.status_label.setText(f"{len(items)} items cargados")

    def on_search(self):
        text = self.search_input.text().strip().lower()
        if not text:
            self.load_items()
            return
        items = db.get_items(500)
        filtered = [it for it in items if text in (it.get("name") or "").lower() or text in (it.get("sku") or "").lower()]
        self.update_table(filtered)
        self.status_label.setText(f"{len(filtered)} resultados")

    def update_table(self, items):
        """Método auxiliar para no repetir código de llenado"""
        self.table.setRowCount(0)
        for it in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(it["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(it.get("sku") or ""))
            self.table.setItem(row, 2, QTableWidgetItem(it.get("name") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(f'{it.get("price",0):,.2f} $'))
            self.table.setItem(row, 4, QTableWidgetItem(f'{it.get("stock",0):,}'))
            self.table.setItem(row, 5, QTableWidgetItem(str(it.get("provider_id") or "")))

    def open_add_item_dialog(self):
        dialog = AddItemDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_data()
                if not data.get("name"):
                    QMessageBox.warning(self, "Nombre requerido", "El campo Nombre es obligatorio.")
                    return
                if data.get("sku") and db.get_item_by_sku(data["sku"]):
                    QMessageBox.warning(self, "SKU duplicado", "Ya existe un ítem con ese SKU.")
                    return

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

    def open_delete_item_dialog(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selección requerida", "Selecciona una fila para eliminar.")
            return

        row = selected_rows[0].row()
        sku_item = self.table.item(row, 1)
        if not sku_item or not sku_item.text():
            QMessageBox.warning(self, "Error", "No se pudo obtener el SKU.")
            return
            
        sku = sku_item.text()
        r = QMessageBox.question(self, "Confirmar", f"¿Eliminar ítem SKU '{sku}'?", QMessageBox.Yes | QMessageBox.No)
        
        if r == QMessageBox.Yes:
            if db.delete_item_by_sku(sku):
                QMessageBox.information(self, "Eliminado", "Ítem eliminado.")
                self.load_items()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar.")

    def on_table_double_click(self, row, col):
        try:
            item_id = self.table.item(row, 0).text()
            stock = self.table.item(row, 4).text()
        except AttributeError:
            return
        
        item_data = db.get_item_by_id(item_id)
        if item_data:
            item_data['id'] = item_id
            item_data['stock'] = stock
            dialog = ItemDetailDialog(item_data, parent=self)
            dialog.exec_()