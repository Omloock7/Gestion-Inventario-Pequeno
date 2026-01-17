from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
    QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import db
from dialogs.dlg_add_item import AddItemDialog
from dialogs.dlg_edit_item import EditItemDialog 
from dialogs.dlg_item_detail import ItemDetailDialog

class InventoryView(QWidget):
    #Estilos
    STYLE_TITLE = "font-size: 22px; font-weight: bold; color: #2c3e50;"
    STYLE_INPUT = "padding-left: 10px; border-radius: 5px; border: 1px solid #bdc3c7;"
    STYLE_BTN_ADD = """
        QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; }
        QPushButton:hover { background-color: #2ecc71; }
    """
    STYLE_BTN_EDIT = """
        QPushButton { background-color: #f39c12; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; }
        QPushButton:hover { background-color: #f1c40f; }
    """
    STYLE_BTN_DEL = """
        QPushButton { background-color: #c0392b; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; }
        QPushButton:hover { background-color: #e74c3c; }
    """
    STYLE_LABEL_STATUS = "color: #7f8c8d; font-style: italic;"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_items()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        main_layout.addLayout(self._create_header())
        main_layout.addLayout(self._create_toolbar())

        self.table = self._create_table()
        main_layout.addWidget(self.table)
        main_layout.addLayout(self._create_footer())

    def _create_header(self):
        layout = QHBoxLayout()
        lbl_title = QLabel("📦 Inventario de Repuestos")
        lbl_title.setStyleSheet(self.STYLE_TITLE)
        
        self.btn_refresh = QPushButton("🔄 Refrescar")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_items)

        layout.addWidget(lbl_title)
        layout.addStretch()
        layout.addWidget(self.btn_refresh)
        return layout

    def _create_toolbar(self):
        layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nombre, SKU o ubicación...")
        self.search_input.setMinimumHeight(35)
        self.search_input.setStyleSheet(self.STYLE_INPUT)
        self.search_input.textChanged.connect(self.on_search_changed)
        
        # BOTÓN AÑADIR
        btn_add = QPushButton("➕ Añadir")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet(self.STYLE_BTN_ADD)
        btn_add.clicked.connect(self.handle_add_item)

        # BOTÓN EDITAR
        btn_edit = QPushButton("✏️ Editar")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet(self.STYLE_BTN_EDIT)
        btn_edit.clicked.connect(self.handle_edit_item)

        # BOTÓN ELIMINAR
        btn_delete = QPushButton("🗑️ Eliminar")
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet(self.STYLE_BTN_DEL)
        btn_delete.clicked.connect(self.handle_delete_item)

        layout.addWidget(self.search_input, stretch=2)
        layout.addSpacing(15)
        layout.addWidget(btn_add)
        layout.addWidget(btn_edit) 
        layout.addWidget(btn_delete)
        return layout

    def _create_table(self):
        table = QTableWidget(0, 9)
        columns = ["ID", "SKU", "Nombre", "Precio", "P. Mayor", "P. Dist", "Stock", "Ubicación", "Proveedor"]
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #2c3e50;  /* Color de fondo (Azul oscuro elegante) */
                color: white;               /* Color de la letra */
                padding: 6px;               /* Espacio de relleno para que no se vea apretado */
                border: 1px solid #34495e;  /* Borde para separar columnas */
                font-weight: bold;          /* Letra en negrita */
                font-size: 12px;            /* Tamaño de letra un poco más grande */
            }
        """)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.cellDoubleClicked.connect(self.handle_table_double_click)
        
        return table

    def _create_footer(self):
        layout = QHBoxLayout()
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet(self.STYLE_LABEL_STATUS)
        layout.addWidget(self.status_label)
        layout.addStretch()
        return layout

    # LÓGICA DE DATOS

    def load_items(self):
        try:
            items = db.get_items(500)
            self._populate_table(items)
            self.status_label.setText(f"Mostrando {len(items)} productos")
        except Exception as e:
            self.status_label.setText("Error de conexión con base de datos")
            print(f"DB Error: {e}")

    def on_search_changed(self):
        text = self.search_input.text().strip().lower()
        items = db.get_items(500)
        
        if not text:
            self._populate_table(items)
            self.status_label.setText(f"Mostrando {len(items)} productos")
            return

        filtered = [
            it for it in items 
            if text in (it.get("name") or "").lower() 
            or text in (it.get("sku") or "").lower()
            or text in (it.get("location") or "").lower()
        ]
        self._populate_table(filtered)
        self.status_label.setText(f"{len(filtered)} resultados encontrados")

    def _populate_table(self, items):
        self.table.setRowCount(0)
        for it in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            price_val = it.get("price", 0.0)
            price_c1 = it.get("price_c1", 0.0)
            price_c2 = it.get("price_c2", 0.0)
            stock_val = it.get("stock", 0)
            location_val = it.get("location", "")
            
            id_item = QTableWidgetItem(str(it["id"]))
            sku_item = QTableWidgetItem(str(it.get("sku") or "S/N"))
            name_item = QTableWidgetItem(str(it.get("name") or ""))
            price_item = QTableWidgetItem(f"$ {price_val:,.2f}")
            p_c1_item = QTableWidgetItem(f"$ {price_c1:,.2f}")
            p_c2_item = QTableWidgetItem(f"$ {price_c2:,.2f}")
            stock_item = QTableWidgetItem(str(stock_val))
            loc_item = QTableWidgetItem(str(location_val))
            # Nombre de proveedor (si viene del JOIN) o el ID
            prov_name = it.get("provider_name") if it.get("provider_name") else str(it.get("provider_id") or "General")
            prov_item = QTableWidgetItem(prov_name)

            id_item.setTextAlignment(Qt.AlignCenter)
            sku_item.setTextAlignment(Qt.AlignCenter)
            price_item.setTextAlignment(Qt.AlignCenter)
            p_c1_item.setTextAlignment(Qt.AlignCenter)
            p_c2_item.setTextAlignment(Qt.AlignCenter)
            stock_item.setTextAlignment(Qt.AlignCenter)
            loc_item.setTextAlignment(Qt.AlignCenter)

            min_alert = it.get("min_stock", 3)
            if min_alert == 0: min_alert = 3 

            if stock_val <= min_alert:
                stock_item.setForeground(QColor("#e67e22"))
                stock_item.setFont(QFont("Arial", weight=QFont.Bold))
            if stock_val <= 0:
                stock_item.setForeground(QColor("#c0392b"))

            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, sku_item)
            self.table.setItem(row, 2, name_item)
            self.table.setItem(row, 3, price_item)
            self.table.setItem(row, 4, p_c1_item)
            self.table.setItem(row, 5, p_c2_item)
            self.table.setItem(row, 6, stock_item)
            self.table.setItem(row, 7, loc_item)
            self.table.setItem(row, 8, prov_item)

    #ACCIONES

    def handle_add_item(self):
        dialog = AddItemDialog(self)
        if dialog.exec_():
            try:
                data = dialog.get_data()
                if not data.get("name"):
                    QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
                    return
                
                db.add_item(
                    sku=data.get("sku"),
                    name=data.get("name"),
                    description=data.get("description"),
                    price=float(data.get("price") or 0),
                    stock=int(data.get("stock") or 0),
                    p_c1=float(data.get("price_c1") or 0),
                    p_c2=float(data.get("price_c2") or 0),
                    provider_id=data.get("provider_id"),
                    min_stock=int(data.get("min_stock") or 0),
                    max_stock=int(data.get("max_stock") or 0),
                    location=data.get("location", "")
                )
                self.load_items()
                QMessageBox.information(self, "Éxito", "Producto guardado correctamente.")

            except ValueError as ve:
                QMessageBox.warning(self, "Aviso", str(ve))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar: {str(e)}")

    def handle_edit_item(self):
        """Lógica para abrir el diálogo de edición con datos cargados"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecciona una fila para editar.")
            return

        row = selected[0].row()
        item_id = int(self.table.item(row, 0).text())
        
        # Obtenemos los datos frescos de la BD antes de editar
        item_data = db.get_item_by_id(item_id)
        
        if item_data:
            dialog = EditItemDialog(item_data, parent=self)
            if dialog.exec_():
                try:
                    # Obtenemos datos modificados
                    new_data = dialog.get_updated_data()
                    
                    if not new_data.get("name"):
                        QMessageBox.warning(self, "Error", "El nombre no puede quedar vacío.")
                        return

                    db.update_item(
                        item_id=new_data['id'],
                        name=new_data['name'],
                        description=new_data['description'],
                        price=new_data['price'],
                        stock=new_data['stock'],
                        p_c1=new_data['price_c1'],
                        p_c2=new_data['price_c2'],
                        provider_id=new_data['provider_id'],
                        min_stock=new_data['min_stock'],
                        max_stock=new_data['max_stock'],
                        location=new_data['location']
                    )
                    
                    self.load_items()
                    QMessageBox.information(self, "Actualizado", "Producto actualizado correctamente.")

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Fallo al actualizar: {e}")

    def handle_delete_item(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecciona una fila para eliminar.")
            return

        row = selected[0].row()
        sku = self.table.item(row, 1).text()
        nombre = self.table.item(row, 2).text()
        
        confirm = QMessageBox.question(
            self, "Confirmar Eliminación", 
            f"¿Estás seguro de eliminar '{nombre}'?", 
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            if db.delete_item_by_sku(sku):
                QMessageBox.information(self, "Éxito", "Producto eliminado.")
                self.load_items()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar.")

    def handle_table_double_click(self, row, col):
        try:
            item_id = self.table.item(row, 0).text()
            item_data = db.get_item_by_id(item_id)
            if item_data:
                dialog = ItemDetailDialog(item_data, parent=self)
                dialog.exec_()
        except Exception as e:
            print(f"Error al abrir detalle: {e}")