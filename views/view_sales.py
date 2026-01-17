from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
    QHeaderView, QAbstractItemView, QDialog, QCalendarWidget
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QBrush
import db

# importar diálogos
try:
    from dialogs.dlg_sale import SaleDialog 
except ImportError:
    SaleDialog = None

try:
    from dialogs.dlg_sale_detail import SaleDetailDialog
except ImportError:
    SaleDetailDialog = None

class SalesView(QWidget):
    # ESTILOS
    STYLE_TITLE = "font-size: 22px; font-weight: bold; color: #2c3e50;"
    STYLE_BTN_NEW = """
        QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; }
        QPushButton:hover { background-color: #2ecc71; }
    """
    STYLE_BTN_FILTER = """
        QPushButton { background-color: #34495e; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; }
        QPushButton:hover { background-color: #2c3e50; }
    """
    STYLE_LABEL_STATUS = "color: #7f8c8d; font-style: italic;"
    STYLE_INPUT = "padding-left: 10px; border-radius: 5px; border: 1px solid #bdc3c7; height: 30px;"

    def __init__(self):
        super().__init__()
        self.all_sales = []
        self.filtered_sales = []
        
        self.date_start = None
        self.date_end = None
        
        self.setup_ui()
        self.load_sales()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        #  Cabecera
        layout.addLayout(self._create_header())
        
        #  Buscador
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por ID, título o método...")
        self.search_input.setStyleSheet(self.STYLE_INPUT)
        self.search_input.textChanged.connect(self.apply_filters)
        layout.addWidget(self.search_input)

        # Tabla de Ventas
        self.table = self._create_table()
        layout.addWidget(self.table)

        # Pie de página
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet(self.STYLE_LABEL_STATUS)
        layout.addWidget(self.status_label)

    def _create_header(self):
        h_layout = QHBoxLayout()
        lbl_title = QLabel("💰 Historial de Ventas")
        lbl_title.setStyleSheet(self.STYLE_TITLE)
        
        self.btn_filter = QPushButton("📅 Filtrar Fechas")
        self.btn_filter.setStyleSheet(self.STYLE_BTN_FILTER)
        self.btn_filter.setCursor(Qt.PointingHandCursor)
        self.btn_filter.clicked.connect(self.open_calendar_filter)

        btn_reset = QPushButton("🔄 Todo")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setFixedWidth(60)
        btn_reset.clicked.connect(self.reset_filters)

        btn_new = QPushButton("➕ Nueva Venta")
        btn_new.setStyleSheet(self.STYLE_BTN_NEW)
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.clicked.connect(self.open_new_sale_dialog)
        
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_filter)
        h_layout.addWidget(btn_reset)
        h_layout.addSpacing(10)
        h_layout.addWidget(btn_new)
        return h_layout

    def _create_table(self):
        table = QTableWidget(0, 5)
        cols = ["ID", "Fecha", "Descripción", "Método", "Total"]
        table.setHorizontalHeaderLabels(cols)
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 6px;
                border: 1px solid #34495e;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter) # Títulos centrados
        
        header.setSectionResizeMode(QHeaderView.ResizeToContents) # ID, Fecha, Metodo, Total ajustados
        header.setSectionResizeMode(2, QHeaderView.Stretch)       
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) 
        
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        table.cellDoubleClicked.connect(self.handle_table_double_click)
        return table

    # --- LÓGICA DE DATOS ---

    def load_sales(self):
        try:
            self.all_sales = db.get_all_sales(limit=1000)
            self.apply_filters()
        except Exception as e:
            print(f"Error cargando ventas: {e}")
            self.status_label.setText("Error de conexión con base de datos.")

    def reset_filters(self):
        self.date_start = None
        self.date_end = None
        self.search_input.clear()
        self.btn_filter.setText("📅 Filtrar Fechas")
        self.apply_filters()

    def open_calendar_filter(self):
        dialog = CalendarRangeDialog(self.date_start, self.date_end, self)
        if dialog.exec_():
            self.date_start, self.date_end = dialog.get_range()
            
            if self.date_start and self.date_end:
                fmt = "dd/MM"
                if self.date_start == self.date_end:
                    self.btn_filter.setText(f"📅 Día: {self.date_start.toString(fmt)}")
                else:
                    self.btn_filter.setText(f"📅 {self.date_start.toString(fmt)} - {self.date_end.toString(fmt)}")
            else:
                self.btn_filter.setText("📅 Filtrar Fechas")
                
            self.apply_filters()

    def apply_filters(self):
        text = self.search_input.text().lower().strip()
        self.filtered_sales = []
        
        for sale in self.all_sales:
            # Filtro Fecha
            if self.date_start and self.date_end:
                sale_date_str = str(sale['created_at'])[:10]
                s_date = QDate.fromString(sale_date_str, "yyyy-MM-dd")
                if not s_date.isValid() or not (self.date_start <= s_date <= self.date_end):
                    continue

            # Filtro Texto
            if text:
                match = (
                    text in str(sale['id']) or 
                    text in str(sale.get('payment_method') or "").lower() or
                    text in str(sale.get('title') or "").lower() # <-- Busca en título
                )
                if not match:
                    continue
            
            self.filtered_sales.append(sale)
            
        self._populate_table(self.filtered_sales)

    def _populate_table(self, sales_list):
        self.table.setRowCount(0)
        total_p = 0.0
        
        for i, sale in enumerate(sales_list):
            self.table.insertRow(i)
            total_p += sale.get('total', 0)
            
            # ID
            id_item = QTableWidgetItem(str(sale['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, id_item)

            # Fecha
            date_item = QTableWidgetItem(str(sale['created_at'])[:16])
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, date_item)
            

            raw_title = sale.get('title')
            title_text = raw_title if raw_title and raw_title.strip() else "Venta General"
            
            title_item = QTableWidgetItem(title_text)
            title_item.setTextAlignment(Qt.AlignCenter)

            if title_text == "Venta General":
                 title_item.setForeground(QColor("#7f8c8d"))
                 title_item.setFont(QFont("Arial", italic=True))
            else:
                 title_item.setFont(QFont("Arial", weight=QFont.Bold))

            self.table.setItem(i, 2, title_item)

            # 3. Método
            method_item = QTableWidgetItem(sale.get('payment_method', '-'))
            method_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 3, method_item)
            
            # 4. Total
            item_total = QTableWidgetItem(f"$ {sale.get('total', 0):,.2f}")
            item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_total.setForeground(QColor("#27ae60"))
            item_total.setFont(QFont("Arial", weight=QFont.Bold))
            self.table.setItem(i, 4, item_total)

        msg = f"Viendo {len(sales_list)} ventas | Total en pantalla: $ {total_p:,.2f}"
        self.status_label.setText(msg)

    def open_new_sale_dialog(self):
        if SaleDialog:
            if SaleDialog(self).exec_(): 
                self.load_sales()
        else:
            print("Error: SaleDialog no importado")

    def handle_table_double_click(self, row, col):
        try:
            sid_item = self.table.item(row, 0)
            if not sid_item: return
            sid = int(sid_item.text())
            sale = next((s for s in self.filtered_sales if s['id'] == sid), None)
            if sale: 
                self.open_detail_dialog(sale)
        except Exception as e:
            print(f"Error al abrir detalle: {e}")

    def open_detail_dialog(self, sale_data):
        if SaleDetailDialog:
            items = db.get_sale_details(sale_data['id'])
            data = dict(sale_data)
            data['client_name'] = "-" 
            SaleDetailDialog(data, items, self).exec_()


# CALENDARIO
class CalendarRangeDialog(QDialog):
    def __init__(self, start_date=None, end_date=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Fechas")
        self.resize(400, 350)
        self.start_date = start_date
        self.end_date = end_date
        self.selection_step = 0
        self.setup_ui()
        if self.start_date and self.end_date:
            self.highlight_range()
            if self.start_date == self.end_date:
                self.lbl_info.setText(f"Seleccionado: {self.start_date.toString('dd/MM/yyyy')}")
            else:
                self.lbl_info.setText(f"Del: {self.start_date.toString('dd/MM')}  Al: {self.end_date.toString('dd/MM')}")
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.lbl_info = QLabel("Haz clic en un día (o dos para rango)")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e; margin-bottom: 5px;")
        layout.addWidget(self.lbl_info)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.clicked.connect(self.on_date_clicked)
        layout.addWidget(self.calendar)

        h_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        self.btn_apply = QPushButton("Aplicar Filtro")
        self.btn_apply.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        self.btn_apply.clicked.connect(self.on_apply_clicked)

        h_layout.addWidget(btn_cancel)
        h_layout.addWidget(self.btn_apply)
        layout.addLayout(h_layout)

    def on_date_clicked(self, date):
        if self.selection_step == 0:
            self.start_date = date
            self.end_date = None
            self.calendar.setDateTextFormat(QDate(), QTextCharFormat()) 
            fmt = QTextCharFormat()
            fmt.setBackground(QBrush(QColor("#2ecc71")))
            fmt.setForeground(QBrush(Qt.white))
            self.calendar.setDateTextFormat(self.start_date, fmt)
            self.lbl_info.setText(f"Inicio: {date.toString('dd/MM')}. Haz clic en otro día para rango, o 'Aplicar'.")
            self.selection_step = 1
        else:
            self.end_date = date
            if self.end_date < self.start_date:
                self.start_date, self.end_date = self.end_date, self.start_date
            self.highlight_range()
            self.lbl_info.setText(f"Rango: {self.start_date.toString('dd/MM')} - {self.end_date.toString('dd/MM')}")
            self.selection_step = 0

    def on_apply_clicked(self):
        if self.start_date and self.end_date is None:
            self.end_date = self.start_date
        self.accept()

    def highlight_range(self):
        if not self.start_date or not self.end_date: return
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        fmt_range = QTextCharFormat()
        fmt_range.setBackground(QBrush(QColor("#d6eaf8"))) 
        fmt_edge = QTextCharFormat()
        fmt_edge.setBackground(QBrush(QColor("#3498db")))
        fmt_edge.setForeground(QBrush(Qt.white))
        fmt_edge.setFontWeight(QFont.Bold)

        curr = self.start_date
        while curr <= self.end_date:
            if curr == self.start_date or curr == self.end_date:
                self.calendar.setDateTextFormat(curr, fmt_edge)
            else:
                self.calendar.setDateTextFormat(curr, fmt_range)
            curr = curr.addDays(1)

    def get_range(self):
        return self.start_date, self.end_date