from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
    QHeaderView, QListWidget, QListWidgetItem, QMessageBox, 
    QGroupBox, QFormLayout, QSplitter, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import db

class ProviderView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_provider_id = None
        self.setup_ui()
        self.load_provider_list()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # PANEL IZQUIERDO: LISTA Y GESTIÓN
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)

        # Título
        lbl_title = QLabel("👥 Proveedores") 
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        left_layout.addWidget(lbl_title)

        # Formulario Rápido
        gb_add = QGroupBox("Nuevo Distribuidor")
        form_layout = QFormLayout()
        self.input_name = QLineEdit()
        self.input_phone = QLineEdit()
        
        btn_add = QPushButton("Guardar")
        btn_add.setStyleSheet("background-color: #27ae60; color: white; border-radius: 4px; padding: 5px;")
        btn_add.clicked.connect(self.handle_add_provider)

        form_layout.addRow("Nombre:", self.input_name)
        form_layout.addRow("Tel:", self.input_phone)
        form_layout.addRow(btn_add)
        gb_add.setLayout(form_layout)
        left_layout.addWidget(gb_add)

        # Lista de Proveedores
        self.list_provider = QListWidget() 
        self.list_provider.itemClicked.connect(self.on_provider_selected)
        left_layout.addWidget(self.list_provider)

        # Botón Eliminar
        btn_del = QPushButton("Eliminar Seleccionado")
        btn_del.setStyleSheet("color: #c0392b; background: transparent; text-align: left;")
        btn_del.clicked.connect(self.handle_delete_provider)
        left_layout.addWidget(btn_del)

        # PANEL DERECHO: REPORTE DE REABASTECIMIENTO
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Cabecera Derecha
        self.lbl_provider_name = QLabel("Selecciona un proveedor")
        self.lbl_provider_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #34495e;")
        
        self.lbl_phone = QLabel("")
        self.lbl_phone.setStyleSheet("color: #7f8c8d; font-size: 14px;")

        right_layout.addWidget(self.lbl_provider_name)
        right_layout.addWidget(self.lbl_phone)
        right_layout.addSpacing(10)

        # Tabla de Reporte
        lbl_report = QLabel("📋 Reporte de Compras")
        lbl_report.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(lbl_report)

        self.table = QTableWidget(0, 5)
        columns = ["SKU", "Producto", "Stock Actual", "Stock Máximo", "A PEDIR"]
        self.table.setHorizontalHeaderLabels(columns)

        #estilos de la tabla
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 6px;
                border: 1px solid #34495e;
                font-weight: bold;
            }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignCenter)          

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.table)

        #UNIR PANELES
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])

        main_layout.addWidget(splitter)

    #LÓGICA 

    def load_provider_list(self):
        self.list_provider.clear()
        providers = db.get_providers() 
        
        for p in providers:
            item = QListWidgetItem(f"{p['name']}")
            item.setData(Qt.UserRole, p)
            self.list_provider.addItem(item)

    def handle_add_provider(self):
        name = self.input_name.text().strip()
        phone = self.input_phone.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return

        try:
            db.add_provider(name, phone)
            self.input_name.clear()
            self.input_phone.clear()
            self.load_provider_list()
            QMessageBox.information(self, "Éxito", "Distribuidor agregado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    def handle_delete_provider(self):
        item = self.list_provider.currentItem()
        if not item: return
        
        data = item.data(Qt.UserRole)
        confirm = QMessageBox.question(self, "Confirmar", f"¿Eliminar a {data['name']}?", QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            db.delete_provider(data['id'])
            self.load_provider_list()
            self.table.setRowCount(0)
            self.lbl_provider_name.setText("Selecciona un proveedor")

    def on_provider_selected(self, item):
        data = item.data(Qt.UserRole)
        self.current_provider_id = data['id']
        
        # Actualizar cabecera
        self.lbl_provider_name.setText(data['name'])
        self.lbl_phone.setText(f"📞 Contacto: {data['phone']}" if data['phone'] else "Sin teléfono")
        
        # Cargar tabla de reporte
        self.load_report_table(data['id'])

    def load_report_table(self, provider_id):
        items = db.get_items_by_provider(provider_id)
        
        self.table.setRowCount(0)
        for it in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            sku_item = QTableWidgetItem(str(it['sku']))
            name_item = QTableWidgetItem(str(it['name']))
            stock_item = QTableWidgetItem(str(it['stock']))
            max_item = QTableWidgetItem(str(it['max_stock']))
            
            qty_needed = it['restock_qty']
            needed_item = QTableWidgetItem(str(qty_needed))
            
            sku_item.setTextAlignment(Qt.AlignCenter)
            name_item.setTextAlignment(Qt.AlignCenter)
            stock_item.setTextAlignment(Qt.AlignCenter)
            max_item.setTextAlignment(Qt.AlignCenter)
            needed_item.setTextAlignment(Qt.AlignCenter)
            
            if qty_needed > 0:
                needed_item.setForeground(QColor("white"))
                needed_item.setBackground(QColor("#e74c3c"))
                needed_item.setFont(QFont("Arial", weight=QFont.Bold))
            else:
                needed_item.setForeground(QColor("#27ae60"))
                needed_item.setFont(QFont("Arial", weight=QFont.Bold))
                needed_item.setText("OK")

            self.table.setItem(row, 0, sku_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, stock_item)
            self.table.setItem(row, 3, max_item)
            self.table.setItem(row, 4, needed_item)