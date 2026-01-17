from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
)

class DeleteItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eliminar Ítem")
        self.setMinimumWidth(300)

        self.sku_input = QLineEdit()

        delete_btn = QPushButton("Eliminar")
        cancel_btn = QPushButton("Cancelar")

        delete_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("SKU del ítem a eliminar:"))
        layout.addWidget(self.sku_input)

        btns = QHBoxLayout()
        btns.addWidget(delete_btn)
        btns.addWidget(cancel_btn)

        layout.addLayout(btns)
        self.setLayout(layout)

    def get_sku(self):
        return self.sku_input.text()
