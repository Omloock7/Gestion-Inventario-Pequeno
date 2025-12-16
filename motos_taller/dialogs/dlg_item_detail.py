# dialogs/dlg_item_detail.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem, QLabel, QTextEdit
from PyQt5.QtCore import Qt

class ItemDetailDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalle Ítem")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Tabla detalle
        self.detail_table = QTableWidget(5, 2)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.setSelectionMode(QTableWidget.NoSelection)
        self.detail_table.horizontalHeader().setVisible(False)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setStyleSheet("QTableWidget { background-color: white; alternate-background-color: #F8F8F8; border: 1px solid #D0D0D0; }")

        # Llenar datos (usando tu lógica formateada)
        data_rows = [
            ("ID", item_data.get('id', 'N/A')),
            ("SKU", item_data.get('sku', 'N/A')),
            ("Nombre", item_data.get('name', 'N/A')),
            ("Stock", item_data.get('stock', 'N/A')),
            ("Precio", f"{item_data.get('price', 0.0):,.2f} $"),
        ]
        
        for i, (name, value) in enumerate(data_rows):
            name_item = QTableWidgetItem(name)
            font = name_item.font()
            font.setBold(True)
            name_item.setFont(font)
            self.detail_table.setItem(i, 0, name_item)
            self.detail_table.setItem(i, 1, QTableWidgetItem(value))
            
        self.detail_table.setFixedHeight(self.detail_table.verticalHeader().defaultSectionSize() * 5 + 2) 
        layout.addWidget(self.detail_table)
        
        # Descripción
        layout.addWidget(QLabel("<b>Descripción:</b>"))
        description_text = item_data.get('description', 'Sin descripción.')
        self.desc_display = QTextEdit()
        self.desc_display.setText(description_text)
        self.desc_display.setReadOnly(True) 
        self.desc_display.setFixedHeight(100) 
        self.desc_display.setStyleSheet("QTextEdit { background-color: #F0F0F0; border: 1px solid #D0D0D0; padding: 5px; }")
        layout.addWidget(self.desc_display)
        
        self.adjustSize()