from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class SalesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("<h1>Módulo de Ventas</h1>")
        title.setStyleSheet("color: purple;")
        layout.addWidget(title)
        layout.addWidget(QLabel("Lógica de ventas aquí..."))
        layout.addStretch()