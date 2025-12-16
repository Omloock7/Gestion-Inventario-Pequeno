from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox
)

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Ítem")
        self.setMinimumWidth(350)

        self.sku_input = QLineEdit()
        self.name_input = QLineEdit()
        
        self.desc_input = QTextEdit()
        self.max_chars = 255 #max caracteres de descripcion
        self.desc_input.textChanged.connect(self.check_text_length)
        #self.desc_input.setMaxLength(100)  no funciona con qtext
        self.desc_input.setFixedHeight(80)   # alto fijo para desc

        
        self.price_input = QLineEdit()
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999)

        save_btn = QPushButton("Guardar")
        cancel_btn = QPushButton("Cancelar")

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("SKU:"))
        layout.addWidget(self.sku_input)

        layout.addWidget(QLabel("Nombre:"))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Descripción:"))
        layout.addWidget(self.desc_input)

        layout.addWidget(QLabel("Precio:"))
        layout.addWidget(self.price_input)

        layout.addWidget(QLabel("Stock inicial:"))
        layout.addWidget(self.stock_input)

        btns = QHBoxLayout()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)

        layout.addLayout(btns)
        self.setLayout(layout)

    def get_data(self):
        return {
            "sku": self.sku_input.text(),
            "name": self.name_input.text(),
            "description": self.desc_input.toPlainText(), 
            "price": float(self.price_input.text()),
            "stock": int(self.stock_input.value())
        }

    def check_text_length(self):
        """
        Verifica la longitud del texto en self.desc_input. 
        Si excede el límite (self.max_chars), trunca el texto.
        """
        current_text = self.desc_input.toPlainText()
        
        if len(current_text) > self.max_chars:
            # 1. Trunca el texto al número máximo de caracteres
            truncated_text = current_text[:self.max_chars]
            
            # 2. Reemplaza el texto en el widget
            self.desc_input.setText(truncated_text)
            
            # 3. Mueve el cursor al final para evitar que el usuario 
            #    siga escribiendo en medio del texto truncado
            cursor = self.desc_input.textCursor()
            cursor.movePosition(cursor.End)
            self.desc_input.setTextCursor(cursor)