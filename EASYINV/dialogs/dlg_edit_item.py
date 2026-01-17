from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QTextEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QSpinBox, QGroupBox, QComboBox, 
    QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, QTimer
import db

class AutoExpandComboBox(QComboBox):
    """
    Se abre automáticamente solo si recibes el foco vía tab.
    """
    def focusInEvent(self, event):
        if event.reason() == Qt.TabFocusReason or event.reason() == Qt.BacktabFocusReason:
            QTimer.singleShot(50, self.showPopup)
        super().focusInEvent(event)

class EditItemDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar Producto: {item_data.get('name', 'Ítem')}")
        self.setMinimumWidth(450)
        self.item_data = item_data 

        #ESTILOS APP
        self.input_style = """
            QLineEdit, QSpinBox, QTextEdit { 
                background-color: white; 
                border: 1px solid #bdc3c7; 
                border-radius: 4px; 
                padding: 4px; 
            }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { 
                border: 2px solid #3498db; 
            }
        """
        
        self.combo_style = """
            QComboBox {
                background-color: white; 
                border: 1px solid #bdc3c7; 
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox:focus { border: 2px solid #3498db; }
            QComboBox::drop-down { border: 0px; }
        """

        # Estilo para campos de solo lectura
        self.readonly_style = """
            QLineEdit { 
                background-color: #ecf0f1; 
                color: #7f8c8d; 
                border: 1px solid #bdc3c7; 
                border-radius: 4px;
                padding: 4px;
            }
        """

        # --- WIDGETS ---
        
        # SKU
        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("SKU")
        self.sku_input.setReadOnly(True) 
        self.sku_input.setStyleSheet(self.readonly_style)

        # Nombre
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del producto")
        self.name_input.setStyleSheet(self.input_style)

        # Proveedor (AutoExpand)
        self.provider_input = AutoExpandComboBox()
        self.provider_input.setStyleSheet(self.combo_style)
        self.load_providers() 

        # Descripción
        self.desc_input = QTextEdit()
        self.max_chars = 255
        self.desc_input.setPlaceholderText("Descripción...")
        self.desc_input.setStyleSheet(self.input_style)
        self.desc_input.textChanged.connect(self.check_text_length)
        self.desc_input.setFixedHeight(60)
        self.desc_input.setTabChangesFocus(True) 
        
        # Ubicación
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ubicación")
        self.location_input.setStyleSheet(self.input_style)

        # Precios
        self.price_c1_input = QLineEdit()
        self.price_c1_input.setStyleSheet(self.input_style)
        self.price_c2_input = QLineEdit()
        self.price_c2_input.setStyleSheet(self.input_style)
        self.price_c3_input = QLineEdit()
        self.price_c3_input.setStyleSheet(self.input_style)

        # Stock
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 99999)
        self.stock_input.setSuffix(" un.")
        self.stock_input.setStyleSheet(self.input_style)

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 9999) 
        # Combinamos estilo base + color naranja
        self.min_stock_input.setStyleSheet(self.input_style + "QSpinBox { color: #e67e22; font-weight: bold; }")
        
        self.max_stock_input = QSpinBox()
        self.max_stock_input.setRange(0, 9999)
        self.max_stock_input.setStyleSheet(self.input_style)

        # Botones
        self.save_btn = QPushButton("💾 Guardar Cambios")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #f39c12; color: white; font-weight: bold; padding: 10px; border-radius: 4px; }
            QPushButton:focus { border: 2px solid #d35400; background-color: #e67e22; }
        """)
        self.save_btn.setAutoDefault(True)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton { padding: 10px; border: 1px solid #bdc3c7; border-radius: 4px; background-color: #ecf0f1; }
            QPushButton:focus { border: 2px solid #95a5a6; }
        """)
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        #LAYOUT PRINCIPAL
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Identificación
        layout.addWidget(QLabel("SKU (Código único - No editable):"))
        layout.addWidget(self.sku_input)
        
        layout.addWidget(QLabel("Nombre del Producto:"))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Proveedor / Distribuidor:"))
        layout.addWidget(self.provider_input)
        
        layout.addWidget(QLabel("Ubicación en Almacén:"))
        layout.addWidget(self.location_input)

        layout.addWidget(QLabel("Descripción:"))
        layout.addWidget(self.desc_input)

        # Precios
        lbl_prices = QLabel("--- Configuración de Precios ---")
        lbl_prices.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_prices)

        h_prices = QHBoxLayout()
        
        v_p1 = QVBoxLayout()
        v_p1.addWidget(QLabel("Precio Público:"))
        v_p1.addWidget(self.price_c1_input)
        
        v_p2 = QVBoxLayout()
        v_p2.addWidget(QLabel("P. Mayorista:"))
        v_p2.addWidget(self.price_c2_input)
        
        v_p3 = QVBoxLayout()
        v_p3.addWidget(QLabel("P. Distribuidor:"))
        v_p3.addWidget(self.price_c3_input)

        h_prices.addLayout(v_p1)
        h_prices.addLayout(v_p2)
        h_prices.addLayout(v_p3)
        layout.addLayout(h_prices)

        #Control de Inventario
        lbl_stock = QLabel("--- Control de Inventario ---")
        lbl_stock.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_stock)

        gb_stock = QGroupBox()
        layout_stock = QHBoxLayout()

        v_stock = QVBoxLayout()
        v_stock.addWidget(QLabel("Stock Actual:"))
        v_stock.addWidget(self.stock_input)
        layout_stock.addLayout(v_stock)

        v_min = QVBoxLayout()
        v_min.addWidget(QLabel("Mínimo:")) 
        v_min.addWidget(self.min_stock_input)
        layout_stock.addLayout(v_min)

        v_max = QVBoxLayout()
        v_max.addWidget(QLabel("Máximo:"))
        v_max.addWidget(self.max_stock_input)
        layout_stock.addLayout(v_max)

        gb_stock.setLayout(layout_stock)
        layout.addWidget(gb_stock)

        # Botones
        layout.addSpacing(10)
        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)
        
        layout.addLayout(btns)
        self.setLayout(layout)

        # --- ORDEN DE TABULACIÓN ---
        QWidget.setTabOrder(self.name_input, self.provider_input)
        QWidget.setTabOrder(self.provider_input, self.location_input)
        QWidget.setTabOrder(self.location_input, self.desc_input)
        QWidget.setTabOrder(self.desc_input, self.price_c1_input)
        QWidget.setTabOrder(self.price_c1_input, self.price_c2_input)
        QWidget.setTabOrder(self.price_c2_input, self.price_c3_input)
        QWidget.setTabOrder(self.price_c3_input, self.stock_input)
        QWidget.setTabOrder(self.stock_input, self.min_stock_input)
        QWidget.setTabOrder(self.min_stock_input, self.max_stock_input)
        QWidget.setTabOrder(self.max_stock_input, self.save_btn)
        QWidget.setTabOrder(self.save_btn, self.cancel_btn)

        #CARGAR DATOS
        self.populate_fields()

    def load_providers(self):
        self.provider_input.clear()
        self.provider_input.addItem("--- General / Sin Asignar ---", None)
        try:
            providers = db.get_providers()
            for p in providers:
                self.provider_input.addItem(p['name'], p['id'])
        except Exception as e:
            print(f"Error cargando proveedores: {e}")

    def populate_fields(self):
        d = self.item_data
        
        self.sku_input.setText(str(d.get('sku', '')))
        self.name_input.setText(str(d.get('name', '')))
        self.desc_input.setText(str(d.get('description', '')))
        self.location_input.setText(str(d.get('location', '')))
        
        self.price_c1_input.setText(str(d.get('price', 0)))
        self.price_c2_input.setText(str(d.get('price_c1', 0)))
        self.price_c3_input.setText(str(d.get('price_c2', 0)))
        
        try:
            self.stock_input.setValue(int(d.get('stock', 0)))
            self.min_stock_input.setValue(int(d.get('min_stock', 0)))
            max_s = int(d.get('max_stock', 0))
            self.max_stock_input.setValue(max_s if max_s > 0 else 100)
        except:
            pass 

        current_prov_id = d.get('provider_id')
        if current_prov_id is not None:
            index = self.provider_input.findData(current_prov_id)
            if index >= 0:
                self.provider_input.setCurrentIndex(index)

    def get_updated_data(self):
        def safe_float(text):
            try: return float(text) if text.strip() else 0.0
            except ValueError: return 0.0

        return {
            "id": self.item_data['id'], 
            "sku": self.sku_input.text().strip(),
            "name": self.name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "location": self.location_input.text().strip(),
            "provider_id": self.provider_input.currentData(), 
            "price": safe_float(self.price_c1_input.text()),   
            "price_c1": safe_float(self.price_c2_input.text()), 
            "price_c2": safe_float(self.price_c3_input.text()), 
            "stock": int(self.stock_input.value()),
            "min_stock": int(self.min_stock_input.value()),
            "max_stock": int(self.max_stock_input.value())
        }

    def check_text_length(self):
        current_text = self.desc_input.toPlainText()
        if len(current_text) > self.max_chars:
            self.desc_input.setText(current_text[:self.max_chars])
            cursor = self.desc_input.textCursor()
            cursor.movePosition(cursor.End)
            self.desc_input.setTextCursor(cursor)