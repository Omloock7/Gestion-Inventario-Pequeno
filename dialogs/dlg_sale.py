from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QHeaderView, 
    QComboBox, QSpinBox, QLineEdit, QMessageBox, QCompleter, QFrame,
    QWidget
)
from PyQt5.QtCore import Qt, QStringListModel, QTimer
import db as db

class AutoExpandComboBox(QComboBox):
    def focusInEvent(self, event):
        if event.reason() == Qt.TabFocusReason or event.reason() == Qt.BacktabFocusReason:
            QTimer.singleShot(50, self.showPopup)
        super().focusInEvent(event)

class SaleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Venta")
        self.setMinimumSize(900, 600)
        
        self.cart = [] 
        self.all_items = [] 
        self.item_map = {} 
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- SECCIÓN SUPERIOR ---
        top_frame = QFrame(self) 
        top_frame.setStyleSheet("background-color: #f1f2f6; border-radius: 8px; padding: 10px;")
        top_layout = QHBoxLayout(top_frame)

        combo_style = """
            QComboBox {
                background-color: white; 
                border: 1px solid #bdc3c7; 
                border-radius: 4px;
                padding: 5px;
                min-width: 150px;
            }
            QComboBox:focus {
                border: 2px solid #3498db; 
            }
            QComboBox::drop-down {
                border: 0px;
            }
        """

        self.cmb_payment = AutoExpandComboBox()
        self.cmb_payment.addItems(["Efectivo", "Transferencia", "Tarjeta", "Crédito"])
        self.cmb_payment.setStyleSheet(combo_style)

        self.input_title = QLineEdit()
        self.input_title.setPlaceholderText("Ej: Cliente Mesa 5, Pedido Juan... (Opcional)")
        self.input_title.setStyleSheet("""
            QLineEdit { background-color: white; padding: 5px; border: 1px solid #bdc3c7; border-radius: 4px; }
            QLineEdit:focus { border: 2px solid #3498db; }
        """)

        top_layout.addWidget(QLabel("Descripción / Ref:"))
        top_layout.addWidget(self.input_title, 1)
        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("Método de Pago:"))
        top_layout.addWidget(self.cmb_payment)
        layout.addWidget(top_frame)

        mid_layout = QHBoxLayout()

        # Buscador
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Buscar producto por nombre o SKU...")
        self.txt_search.setStyleSheet("""
            QLineEdit { padding: 5px; border: 1px solid #bdc3c7; border-radius: 4px; }
            QLineEdit:focus { border: 2px solid #3498db; }
        """)
        
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.txt_search.setCompleter(self.completer)


        # carga datos cuando se selecciona del autocompletado o cuando se escribe 
        self.completer.activated.connect(self.on_product_selected)
        self.txt_search.textChanged.connect(self.on_text_changed)
        
        # Selector de TIPO DE PRECIO
        self.cmb_price_type = AutoExpandComboBox()
        self.cmb_price_type.addItems([
            "Precio Público ($ 0)", 
            "P. Mayorista ($ 0)", 
            "P. Distribuidor ($ 0)"
        ])
        self.cmb_price_type.setToolTip("Selecciona la tarifa a aplicar")
        self.cmb_price_type.setStyleSheet(combo_style)

        # Cantidad
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 9999)
        self.spin_qty.setValue(1)
        self.spin_qty.setFixedWidth(80)
        self.spin_qty.setStyleSheet("""
            QSpinBox { padding: 5px; border: 1px solid #bdc3c7; border-radius: 4px; background-color: white; }
            QSpinBox:focus { border: 2px solid #3498db; }
        """)

        btn_add = QPushButton("Agregar [Enter]")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; padding: 6px; border-radius: 4px; } 
            QPushButton:focus { border: 2px solid #2c3e50; background-color: #2980b9; }
            QPushButton:pressed { background-color: #1abc9c; }
        """)
        btn_add.clicked.connect(self.add_item_to_cart)
        btn_add.setAutoDefault(True)

        mid_layout.addWidget(QLabel("Producto:"))
        mid_layout.addWidget(self.txt_search, 3)
        mid_layout.addWidget(QLabel("Tarifa:"))
        mid_layout.addWidget(self.cmb_price_type, 1)
        mid_layout.addWidget(QLabel("Cant:"))
        mid_layout.addWidget(self.spin_qty)
        mid_layout.addWidget(btn_add)

        layout.addLayout(mid_layout)

        # TABLA
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Producto", "Tarifa", "Cant.", "P. Unit.", "Subtotal"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnHidden(0, True)
        
        self.table.doubleClicked.connect(self.remove_row)
        layout.addWidget(self.table)

        # FOOTER
        bottom_layout = QHBoxLayout()
        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 24px; font-weight: bold; color: #27ae60;")
        
        self.btn_save = QPushButton("Confirmar Venta")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setMinimumHeight(50)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; font-size: 16px; font-weight: bold; border-radius: 5px; } 
            QPushButton:focus { border: 3px solid #1e8449; background-color: #27ae60; }
        """)
        self.btn_save.clicked.connect(self.save_sale)
        self.btn_save.setAutoDefault(True)

        bottom_layout.addWidget(self.lbl_total)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_save, 1)

        layout.addLayout(bottom_layout)

        QWidget.setTabOrder(self.input_title, self.cmb_payment)
        QWidget.setTabOrder(self.cmb_payment, self.txt_search)
        QWidget.setTabOrder(self.txt_search, self.cmb_price_type)
        QWidget.setTabOrder(self.cmb_price_type, self.spin_qty)
        QWidget.setTabOrder(self.spin_qty, btn_add)
        QWidget.setTabOrder(btn_add, self.btn_save)

    def load_data(self):
        self.all_items = db.get_items(limit=1000) 
        
        search_list = []
        self.item_map = {} 
        
        for item in self.all_items:
            display_text = f"{item['sku']} | {item['name']} (Stock: {item['stock']})"
            search_list.append(display_text)
            self.item_map[display_text] = item
            
        model = QStringListModel(search_list)
        self.completer.setModel(model)

    # Función auxiliar para actualizar los textos del combo
    def update_price_labels(self, p1=0, p2=0, p3=0):
        # Mantenemos el índice seleccionado actual para que no salte
        current_idx = self.cmb_price_type.currentIndex()
        
        self.cmb_price_type.setItemText(0, f"Precio Público (${float(p1):,.0f})")
        self.cmb_price_type.setItemText(1, f"P. Mayorista (${float(p2):,.0f})")
        self.cmb_price_type.setItemText(2, f"P. Distribuidor (${float(p3):,.0f})")
        
        self.cmb_price_type.setCurrentIndex(current_idx)

    # Se ejecuta al seleccionar del autocompletado
    def on_product_selected(self, text):
        if text in self.item_map:
            item = self.item_map[text]
            self.update_price_labels(
                item.get('price', 0),
                item.get('price_c1', 0),
                item.get('price_c2', 0)
            )

    # Si el texto coincide exactamente con una clave, actualizamos
    def on_text_changed(self, text):

        if text in self.item_map:
            self.on_product_selected(text)
        else:
            # Si no coincide (está escribiendo o borró), ponemos todo en 0
            self.update_price_labels(0, 0, 0)

    def add_item_to_cart(self):
        text = self.txt_search.text()
        
        if text not in self.item_map:
            QMessageBox.warning(self, "Error", "Selecciona un producto válido del buscador.")
            return

        selected_item = self.item_map[text]
        qty = self.spin_qty.value()
        
        if selected_item['stock'] < qty:
            QMessageBox.warning(self, "Stock Insuficiente", f"Solo quedan {selected_item['stock']} unidades disponibles.")
            return

        # Determinar PRECIO
        price_index = self.cmb_price_type.currentIndex()
        final_price = 0.0
        price_label = ""

        if price_index == 0:   # Público
            final_price = selected_item['price']
            price_label = "Público"
        elif price_index == 1: # Mayorista
            final_price = selected_item.get('price_c1', 0)
            price_label = "Mayorista"
        elif price_index == 2: # Distribuidor
            final_price = selected_item.get('price_c2', 0)
            price_label = "Distribuidor"

        if final_price <= 0:
            res = QMessageBox.question(self, "Precio Cero", 
                f"El precio seleccionado ({price_label}) es $0. ¿Deseas continuar?", 
                QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.No: return

        # Agregar al carrito
        subtotal = final_price * qty
        
        row_data = {
            'id': selected_item['id'],
            'name': selected_item['name'],
            'price_label': price_label,
            'qty': qty,
            'price': final_price,
            'subtotal': subtotal
        }
        
        self.cart.append(row_data)
        self.refresh_cart_table()
        
        # Reiniciar para siguiente producto
        self.txt_search.clear()
        self.spin_qty.setValue(1)
        self.update_price_labels(0, 0, 0) # Volver a 0 visualmente
        self.txt_search.setFocus() 

    def refresh_cart_table(self):
        self.table.setRowCount(0)
        total_gral = 0.0
        
        for i, item in enumerate(self.cart):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(item['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(item['name']))
            self.table.setItem(i, 2, QTableWidgetItem(item['price_label']))
            self.table.setItem(i, 3, QTableWidgetItem(str(item['qty'])))
            self.table.setItem(i, 4, QTableWidgetItem(f"${item['price']:,.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"${item['subtotal']:,.2f}"))
            
            total_gral += item['subtotal']
            
        self.lbl_total.setText(f"Total: ${total_gral:,.2f}")

    def remove_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.cart.pop(row)
            self.refresh_cart_table()

    def save_sale(self):
        if not self.cart:
            QMessageBox.warning(self, "Error", "El carrito está vacío.")
            return

        try:
            client_id = 0 
            payment_method = self.cmb_payment.currentText()
            
            user_title = self.input_title.text().strip()
            title = user_title if user_title else "Venta General"
            
            db.register_sale(title, client_id, self.cart, payment_method)
            
            QMessageBox.information(self, "Éxito", "Venta registrada correctamente.")
            self.accept() 
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la venta:\n{str(e)}")
            
            