from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt

class SaleDetailDialog(QDialog):
    def __init__(self, sale_data, items_sold, parent=None):
        super().__init__(parent)
        # Usamos .get() por seguridad. Si no hay ID, pone '?'
        sale_id = sale_data.get('id', '?')
        self.setWindowTitle(f"Detalle de Venta #{sale_id}")
        self.setMinimumSize(600, 450)
        
        self.sale_data = sale_data
        self.items_sold = items_sold
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # INFORMACIÓN DE CABECERA
        header = QVBoxLayout()
        
        # USO DE .get() PARA EVITAR EL ERROR (KEYERROR)
        # Si 'title' no existe en el diccionario, usa 'Venta General'
        title_text = self.sale_data.get('title') or 'Venta General'
        title_label = QLabel(f"<b>Venta:</b> {title_text}")
        title_label.setStyleSheet("font-size: 18px; color: #2c3e50;")
        
        info_layout = QHBoxLayout()
        
        # Extraemos datos con seguridad
        date_str = str(self.sale_data.get('created_at', ''))
        client_str = str(self.sale_data.get('client_name') or 'Cliente General')
        pay_method = str(self.sale_data.get('payment_method', 'Efectivo'))
        sale_id = str(self.sale_data.get('id', '-'))

        info_left = QLabel(
            f"<b>Fecha:</b> {date_str}<br>"
            f"<b>Cliente:</b> {client_str}"
        )
        info_right = QLabel(
            f"<b>Método:</b> {pay_method}<br>"
            f"<b>ID Transacción:</b> {sale_id}"
        )
        # Estilo para mejor lectura
        info_left.setStyleSheet("font-size: 13px; padding: 5px;")
        info_right.setStyleSheet("font-size: 13px; padding: 5px;")

        info_layout.addWidget(info_left)
        info_layout.addWidget(info_right)
        
        header.addWidget(title_label)
        header.addLayout(info_layout)
        
        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        header.addWidget(line)
        
        layout.addLayout(header)

        layout.addWidget(QLabel("<b>Productos vendidos:</b>"))

        #TABLA DE PRODUCTOS
        self.table = QTableWidget(len(self.items_sold), 4)
        self.table.setHorizontalHeaderLabels(["Producto", "Cant.", "P. Unitario", "Subtotal"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        for row, item in enumerate(self.items_sold):
            # Usamos .get() también aquí por seguridad
            name = item.get('item_name', 'Item ???')
            qty = item.get('qty', 0)
            price = item.get('unit_price', 0.0)
            subtotal = item.get('subtotal', qty * price)

            self.table.setItem(row, 0, QTableWidgetItem(str(name)))
            self.table.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.table.setItem(row, 2, QTableWidgetItem(f"$ {price:,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"$ {subtotal:,.2f}"))

        layout.addWidget(self.table)

        # --- TOTAL FINAL ---
        total_val = self.sale_data.get('total', 0.0)
        total_label = QLabel(f"TOTAL: $ {total_val:,.2f}")
        total_label.setAlignment(Qt.AlignRight)
        total_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #27ae60; margin-top: 10px;")
        layout.addWidget(total_label)

        # Botón Cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("padding: 8px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)