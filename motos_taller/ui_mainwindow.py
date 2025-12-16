from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton
import db

# Importes de visstas desde views
from views.view_inventory import InventoryView
from views.view_sales import SalesView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Taller Motos")
        self.resize(900, 600)
        db.init_db()

        # Configuración UI Principal
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QVBoxLayout(main_container)

        # barra de Navegación
        self.nav_layout = QHBoxLayout()
        self.btn_inventory = QPushButton("Inventario")
        self.btn_sales = QPushButton("Ventas")
        
        self.nav_layout.addWidget(self.btn_inventory)
        self.nav_layout.addWidget(self.btn_sales)
        self.nav_layout.addStretch()
        main_layout.addLayout(self.nav_layout)

        # Contenedor de Vistas
        self.stacked_widget = QStackedWidget()
        
        # inicializa las clases de las vistas
        self.view_inventory = InventoryView()
        self.view_sales = SalesView()
        
        # Las añadimos al Stack (Índice 0 e Índice 1)
        self.stacked_widget.addWidget(self.view_inventory)
        self.stacked_widget.addWidget(self.view_sales)
        
        main_layout.addWidget(self.stacked_widget)

        # 3. Conexiones
        self.btn_inventory.clicked.connect(lambda: self.switch_view(0))
        self.btn_sales.clicked.connect(lambda: self.switch_view(1))
        
        # Estilo inicial
        self.switch_view(0)

    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)
        
        # Estilos visuales para saber en qué pestaña estamos
        active_style = "font-weight: bold; color: black;"
        default_style = ""
        
        if index == 0:
            self.btn_inventory.setStyleSheet(active_style)
            self.btn_sales.setStyleSheet(default_style)
        elif index == 1:
            self.btn_sales.setStyleSheet(active_style)
            self.btn_inventory.setStyleSheet(default_style)