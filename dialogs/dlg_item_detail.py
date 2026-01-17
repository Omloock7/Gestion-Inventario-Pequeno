from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLabel, QTextEdit, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

class ItemDetailDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalle del Repuesto")
        self.setMinimumWidth(500)
        self.item_data = item_data
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        header = QLabel(f"📋 {self.item_data.get('name', 'Producto')}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Tabla de detalles
        self.table = QTableWidget(11, 2)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { gridline-color: #bdc3c7; }")

        # Helpers para formatear dinero y nulos
        def fmt_price(val):
            return f"$ {float(val):,.2f}" if val else "$ 0.00"
        
        def fmt_str(val):
            return str(val) if val is not None else ""

        # Datos organizados
        rows = [
            ("ID Sistema", fmt_str(self.item_data.get('id'))),
            ("Código SKU", fmt_str(self.item_data.get('sku'))),
            ("Ubicación", fmt_str(self.item_data.get('location'))),
            ("Stock Actual", fmt_str(self.item_data.get('stock'))),
            ("Stock Mínimo", fmt_str(self.item_data.get('min_stock'))),
            ("Stock Máximo", fmt_str(self.item_data.get('max_stock'))), 
            ("Precio Público", fmt_price(self.item_data.get('price'))),
            ("P. Mayorista", fmt_price(self.item_data.get('price_c1'))),
            ("P. Distribuidor", fmt_price(self.item_data.get('price_c2'))),
            ("Proveedor ID", fmt_str(self.item_data.get('provider_id') or "N/A")),
            ("Fecha Alta", fmt_str(self.item_data.get('created_at')))
        ]

        bold_font = QFont()
        bold_font.setBold(True)

        for i, (label, val) in enumerate(rows):
            # Columna Etiqueta
            lbl_item = QTableWidgetItem(label)
            lbl_item.setFont(bold_font)
            lbl_item.setBackground(QColor("#ecf0f1"))
            self.table.setItem(i, 0, lbl_item)
            
            # Columna Valor
            val_item = QTableWidgetItem(val)
            val_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            # Lógica visual de colores
            if label == "Stock Actual":
                stock_val = int(self.item_data.get('stock', 0))
                min_val = int(self.item_data.get('min_stock', 0))
                
                val_item.setFont(bold_font)
                if stock_val <= 0:
                    val_item.setForeground(QColor("#c0392b"))
                elif stock_val <= min_val:
                    val_item.setForeground(QColor("#e67e22"))
                else:
                    val_item.setForeground(QColor("#27ae60"))
            
            if label == "Ubicación" and val == "":
                val_item.setText("--- Sin asignar ---")
                val_item.setForeground(QColor("#95a5a6"))

            self.table.setItem(i, 1, val_item)
            
        self.table.setFixedHeight(350)
        layout.addWidget(self.table)

        # Descripción
        layout.addWidget(QLabel("<b>Descripción detallada:</b>"))
        desc = QTextEdit()
        desc.setText(str(self.item_data.get('description', 'Sin descripción.')))
        desc.setReadOnly(True)
        desc.setFixedHeight(80)
        desc.setStyleSheet("background-color: #f9f9f9;")
        layout.addWidget(desc)

        # Botón Cerrar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn = QPushButton("Cerrar")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #34495e; color: white; padding: 8px 20px; border-radius: 4px; }
            QPushButton:hover { background-color: #2c3e50; }
        """)
        btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)