from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QTextEdit, QPushButton, 
    QTableWidget, QVBoxLayout, QHBoxLayout, QSpinBox, 
    QGroupBox, QComboBox, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt, QEvent, QTimer
import db

class AutoExpandComboBox(QComboBox):
    """
    Se abre automáticamente solo si recibes el foco vía tab
    """
    def focusInEvent(self, event):
        if event.reason() == Qt.TabFocusReason or event.reason() == Qt.BacktabFocusReason:
            QTimer.singleShot(50, self.showPopup)
        super().focusInEvent(event)

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Nuevo Ítem")
        self.setMinimumWidth(450) # Un poco más ancho para que se vea bien

        #estilos de la app
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

        #CAMPOS BASICOS
        
        # SKU
        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Ej: USB-KING-32GB")
        self.sku_input.setStyleSheet(self.input_style)
        
        # Nombre
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Memoria USB 32GB")
        self.name_input.setStyleSheet(self.input_style)

        # Selección de proveedor (Usando AutoExpand)
        self.provider_input = AutoExpandComboBox()
        self.provider_input.setStyleSheet(self.combo_style)
        self.load_providers() 

        # Ubicación
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Estante A, Nivel 2")
        self.location_input.setStyleSheet(self.input_style)

        # Descripción
        self.desc_input = QTextEdit()
        self.max_chars = 255
        self.desc_input.setPlaceholderText("Descripción detallada del producto...")
        self.desc_input.setStyleSheet(self.input_style)
        self.desc_input.textChanged.connect(self.check_text_length)
        self.desc_input.setFixedHeight(60)
        #para que tab funcione bien en QTextEdit
        self.desc_input.setTabChangesFocus(True) 

        # --- 2. PRECIOS ---
        self.price_c1_input = QLineEdit()
        self.price_c1_input.setPlaceholderText("0.00")
        self.price_c1_input.setStyleSheet(self.input_style)
        
        self.price_c2_input = QLineEdit()
        self.price_c2_input.setPlaceholderText("0.00 (Opcional)")
        self.price_c2_input.setStyleSheet(self.input_style)
        
        self.price_c3_input = QLineEdit()
        self.price_c3_input.setPlaceholderText("0.00 (Opcional)")
        self.price_c3_input.setStyleSheet(self.input_style)

        # STOCK Y LIMITES
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 9999)
        self.stock_input.setSuffix(" un.")
        self.stock_input.setStyleSheet(self.input_style)

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(1, 999) 
        self.min_stock_input.setValue(1) 
        #alerta en color naranja
        self.min_stock_input.setStyleSheet(self.input_style + "QSpinBox { color: #e67e22; font-weight: bold; }")

        self.max_stock_input = QSpinBox()
        self.max_stock_input.setRange(1, 999)
        self.max_stock_input.setValue(100)
        self.max_stock_input.setStyleSheet(self.input_style)

        #BOTONES
        self.save_btn = QPushButton("Guardar Producto")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 10px; border-radius: 4px;}
            QPushButton:focus { border: 2px solid #1e8449; background-color: #219150; }
        """)
        self.save_btn.setAutoDefault(True) # Permite activar con Enter
        
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
        layout.addWidget(QLabel("SKU (Código único):"))
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

        # Control de Inventario
        lbl_stock = QLabel("--- Control de Inventario ---")
        lbl_stock.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_stock)

        gb_stock = QGroupBox()
        layout_stock = QHBoxLayout()

        v_stock = QVBoxLayout()
        v_stock.addWidget(QLabel("Stock Inicial:"))
        v_stock.addWidget(self.stock_input)
        layout_stock.addLayout(v_stock)

        v_min = QVBoxLayout()
        v_min.addWidget(QLabel("Mínimo (Alerta):")) 
        v_min.addWidget(self.min_stock_input)
        layout_stock.addLayout(v_min)

        v_max = QVBoxLayout()
        v_max.addWidget(QLabel("Máximo Permitido:"))
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

        # --- ORDEN DE TABULACIÓN (TAB ORDER) ---
        QWidget.setTabOrder(self.sku_input, self.name_input)
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

    def load_providers(self):
        self.provider_input.clear()
        self.provider_input.addItem("--- General / Sin Asignar ---", None)
        try:
            providers = db.get_providers()
            for p in providers:
                self.provider_input.addItem(p['name'], p['id'])
        except Exception as e:
            print(f"Error cargando proveedores: {e}")

    def get_data(self):
        def safe_float(text):
            try:
                return float(text) if text.strip() else 0.0
            except ValueError:
                return 0.0

        return {
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
            truncated_text = current_text[:self.max_chars]
            self.desc_input.setText(truncated_text)
            cursor = self.desc_input.textCursor()
            cursor.movePosition(cursor.End)
            self.desc_input.setTextCursor(cursor)