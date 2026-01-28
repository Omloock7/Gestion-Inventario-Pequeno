from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QStackedWidget, QLabel, QFrame,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

# --- IMPORTACIONES DE VISTAS ---
try:
    from views.view_inventory import InventoryView
    from views.view_sales import SalesView
    from views.view_advanced import AdvancedView
    from views.view_provider import ProviderView 
except ImportError as e:
    print(f"ERROR IMPORTS: {e}")
    InventoryView = None
    SalesView = None
    AdvancedView = None
    ProviderView = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EASYINV v2.1")
        self.resize(1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.setup_top_bar()
        self.setup_content_area()
        
        self.switch_view(0)

    def setup_top_bar(self):
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(70)
        self.top_bar.setStyleSheet("""
            QFrame { background-color: #2c3e50; border-bottom: 3px solid #34495e; }
            QPushButton { background-color: transparent; color: #ecf0f1; font-size: 16px; font-weight: bold; padding: 10px 20px; border: none; border-radius: 4px; }
            QPushButton:hover { background-color: #34495e; color: white; }
            QPushButton:pressed { background-color: #1abc9c; }
        """)
        
        bar_layout = QHBoxLayout(self.top_bar)
        bar_layout.setContentsMargins(10, 0, 10, 0)
        
        # --- BOTONES ---
        self.btn_inv = QPushButton("📦 Inventario")
        self.btn_inv.setCursor(Qt.PointingHandCursor)
        self.btn_inv.clicked.connect(lambda: self.switch_view(0))
        
        self.btn_sales = QPushButton("💰 Ventas")
        self.btn_sales.setCursor(Qt.PointingHandCursor)
        self.btn_sales.clicked.connect(lambda: self.switch_view(1))

        self.btn_provider = QPushButton("👥 Distribuidor") 
        self.btn_provider.setCursor(Qt.PointingHandCursor)
        self.btn_provider.clicked.connect(lambda: self.switch_view(3))

        self.btn_advanced = QPushButton("🔧 Avanzado")
        self.btn_advanced.setCursor(Qt.PointingHandCursor)
        self.btn_advanced.clicked.connect(lambda: self.switch_view(2))
        # --- TÍTULO ---
        lbl_title = QLabel("EASYINV v2.1")
        lbl_title.setStyleSheet("color: #bdc3c7; font-weight: bold;")
        
        bar_layout.addWidget(self.btn_inv)
        bar_layout.addWidget(self.btn_sales)
        bar_layout.addWidget(self.btn_provider) 
        bar_layout.addWidget(self.btn_advanced)
        bar_layout.addStretch()
        bar_layout.addWidget(lbl_title)
        
        self.main_layout.addWidget(self.top_bar)

    def setup_content_area(self):
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        #Inventario
        if InventoryView:
            self.view_inventory = InventoryView()
            self.stacked_widget.addWidget(self.view_inventory)
        else:
            self.stacked_widget.addWidget(QLabel("Error Inventario"))
            
        #Ventas
        if SalesView:
            self.view_sales = SalesView()
            self.stacked_widget.addWidget(self.view_sales)
        else:
            self.stacked_widget.addWidget(QLabel("Error Ventas"))

        #Avanzado
        if AdvancedView:
            self.view_advanced = AdvancedView()
            self.stacked_widget.addWidget(self.view_advanced)
        else:
            self.stacked_widget.addWidget(QLabel("Error Vista Avanzada"))

        #Provider
        if ProviderView:
            self.view_provider = ProviderView() 
            self.stacked_widget.addWidget(self.view_provider)
        else:
            self.stacked_widget.addWidget(QLabel("Error Vista Distribuidor"))

    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)
        
        if index == 0 and hasattr(self, 'view_inventory'):
            self.view_inventory.load_items()
        elif index == 1 and hasattr(self, 'view_sales'):
            self.view_sales.load_sales()
        elif index == 2 and hasattr(self, 'view_advanced'):
            self.view_advanced.load_log_preview()
        elif index == 3 and hasattr(self, 'view_provider'): 
            self.view_provider.load_provider_list()