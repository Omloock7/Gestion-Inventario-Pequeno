import sqlite3
import os
import sys
import shutil
from contextlib import closing
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
from PyQt5.QtSql import QSqlDatabase 

# ==============================================================================
# 1. GESTIÓN DE RUTAS Y DIRECTORIOS (CRÍTICO PARA EL EXE VS DEV)
# ==============================================================================

APP_FOLDER_NAME = "EasyINV"

# Detectamos si estamos en un EXE (Frozen) o en Código (Dev)
if getattr(sys, 'frozen', False):
    # --- MODO EXE (Producción) ---
    # Los recursos estáticos están en _MEIPASS
    BUNDLE_DIR = sys._MEIPASS 
    EXE_DIR = os.path.dirname(sys.executable)
    
    # En producción, OBLIGAMOS a usar AppData para tener permisos de escritura
    USER_DATA_DIR = os.path.join(os.getenv('APPDATA'), APP_FOLDER_NAME)
    
    # Crear carpeta en AppData si no existe
    if not os.path.exists(USER_DATA_DIR):
        try:
            os.makedirs(USER_DATA_DIR)
        except OSError:
            # Fallback a carpeta de usuario si AppData falla
            USER_DATA_DIR = os.path.join(os.path.expanduser("~"), APP_FOLDER_NAME)
            os.makedirs(USER_DATA_DIR, exist_ok=True)

else:
    # --- MODO DESARROLLO (Visual Studio Code) ---
    # Usamos la carpeta local del proyecto para no ensuciar AppData mientras programas
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BUNDLE_DIR
    USER_DATA_DIR = BUNDLE_DIR  # <--- Esto hace que la DB se guarde junto a tu código

# ESTA ES LA RUTA FINAL QUE USARÁ TODO EL SISTEMA
DB_PATH = os.path.join(USER_DATA_DIR, "inventory.db")

# ==============================================================================

def get_db_connection() -> sqlite3.Connection:
    """Devuelve una conexión a la base de datos en la ruta segura."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inicializa la base de datos.
    1. Si no existe en la ruta destino, intenta copiar una plantilla.
    2. Si no hay plantilla, crea las tablas desde cero.
    3. Configura la conexión QtSql para la interfaz gráfica.
    """
    
    # --- PASO 1: GESTIÓN DE ARCHIVOS ---
    if not os.path.exists(DB_PATH):
        print(f"Base de datos no encontrada en {DB_PATH}. Inicializando...")
        
        # Buscamos si existe una plantilla 'inventory.db' (útil para actualizaciones del EXE)
        candidates = [
            os.path.join(EXE_DIR, "inventory.db"),
            os.path.join(BUNDLE_DIR, "inventory.db")
        ]
        
        copied = False
        for candidate in candidates:
            # Evitamos copiarnos a nosotros mismos en modo desarrollo
            if os.path.abspath(candidate) == os.path.abspath(DB_PATH):
                continue

            if os.path.exists(candidate):
                try:
                    shutil.copy2(candidate, DB_PATH)
                    print(f"Plantilla copiada exitosamente de: {candidate}")
                    copied = True
                    break
                except Exception as e:
                    print(f"Error al copiar plantilla: {e}")
        
        if not copied:
            print("No se encontró plantilla externa. Se creará una base de datos nueva.")

    # --- PASO 2: CREACIÓN DE TABLAS (Solo si no existen) ---
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        
        # 1. Tabla de Productos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                provider_id INTEGER,
                created_at TEXT,
                active INTEGER DEFAULT 1,
                price_c1 REAL DEFAULT 0,
                price_c2 REAL DEFAULT 0,
                min_stock INTEGER DEFAULT 0,
                max_stock INTEGER DEFAULT 0,
                location TEXT DEFAULT ''
            )
        """)

        # 2. Tabla de encabezados de Ventas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                client_id INTEGER,
                total REAL,
                payment_method TEXT,
                created_at TEXT
            )
        """)

        # 3. Detalle de Ventas 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                item_id INTEGER,
                item_name TEXT, 
                qty INTEGER,
                unit_price REAL,
                FOREIGN KEY(sale_id) REFERENCES sales(id),
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        """)

        # 4. Tabla de Proveedores
        cur.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                created_at TEXT,
                active INTEGER DEFAULT 1
            )
        """)
        conn.commit()

    # --- PASO 3: INICIALIZAR CONEXIÓN QT (PARA LA GUI) ---
    if QSqlDatabase.contains("qt_sql_default_connection"):
        db = QSqlDatabase.database("qt_sql_default_connection")
    else:
        db = QSqlDatabase.addDatabase("QSQLITE")
    
    db.setDatabaseName(DB_PATH)
    
    if not db.open():
        print(f"ERROR CRÍTICO: QtSql no pudo abrir la DB en {DB_PATH}")
        print(db.lastError().text())
    else:
        print(f"Conexión QtSql establecida correctamente en: {DB_PATH}")

    print("Inicialización de DB completada.")

# ==============================================================================
# FUNCIONES DE LÓGICA DE NEGOCIO 
# ==============================================================================

def add_provider(name: str, phone: str) -> int:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO providers (name, phone, created_at, active) VALUES (?, ?, ?, 1)", 
                    (name, phone, now))
        conn.commit()
        return cur.lastrowid

def get_providers() -> List[Dict[str, Any]]:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM providers WHERE active = 1 ORDER BY name ASC")
        return [dict(row) for row in cur.fetchall()]

def update_provider(provider_id: int, name: str, phone: str) -> bool:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE providers SET name = ?, phone = ? WHERE id = ?", (name, phone, provider_id))
        conn.commit()
        return cur.rowcount > 0

def delete_provider(provider_id: int) -> bool:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE providers SET active = 0 WHERE id = ?", (provider_id,))
        conn.commit()
        return cur.rowcount > 0

def get_items_by_provider(provider_id: int) -> List[Dict[str, Any]]:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        query = """
            SELECT id, sku, name, stock, min_stock, max_stock 
            FROM items 
            WHERE provider_id = ? AND active = 1
            ORDER BY name ASC
        """
        cur.execute(query, (provider_id,))
        rows = cur.fetchall()
        
        result = []
        for row in rows:
            item = dict(row)
            needed = 0
            if item['max_stock'] > 0:
                needed = item['max_stock'] - item['stock']
                if needed < 0: needed = 0
            
            item['restock_qty'] = needed
            result.append(item)
            
        return result

def add_item(sku: str, name: str, description: str, price: float, stock: int, 
             p_c1: float = 0, p_c2: float = 0, provider_id: Optional[int] = None,
             min_stock: int = 0, max_stock: int = 0, location: str = "") -> int:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, active FROM items WHERE sku = ?", (sku,))
        row = cur.fetchone()
        
        if row:
            item_id = row['id']
            if row['active'] == 1:
                raise ValueError(f"El SKU '{sku}' ya existe y está activo.")
            
            # Reactivar ítem si estaba borrado
            query = """
                UPDATE items 
                SET name=?, description=?, price=?, stock=?, 
                    price_c1=?, price_c2=?, provider_id=?, 
                    min_stock=?, max_stock=?, location=?,
                    active=1, created_at=?
                WHERE id=?
            """
            cur.execute(query, (name, description, price, stock, p_c1, p_c2, provider_id, 
                                min_stock, max_stock, location, now, item_id))
            conn.commit()
            return item_id
        
        else:
            # Crear ítem nuevo con todas las columnas
            query = """
                INSERT INTO items (
                    sku, name, description, price, stock, 
                    price_c1, price_c2, provider_id, created_at, active,
                    min_stock, max_stock, location
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """
            cur.execute(query, (sku, name, description, price, stock, p_c1, p_c2, provider_id, now, 
                                min_stock, max_stock, location))
            conn.commit()
            return cur.lastrowid

def update_item(item_id: int, name: str, description: str, price: float, stock: int,
                p_c1: float, p_c2: float, provider_id: Optional[int],
                min_stock: int, max_stock: int, location: str) -> bool:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        query = """
            UPDATE items 
            SET name=?, description=?, price=?, stock=?, 
                price_c1=?, price_c2=?, provider_id=?,
                min_stock=?, max_stock=?, location=?
            WHERE id=?
        """
        cur.execute(query, (name, description, price, stock, p_c1, p_c2, provider_id, 
                            min_stock, max_stock, location, item_id))
        conn.commit()
        return cur.rowcount > 0

def get_items(limit: int = 500) -> List[Dict[str, Any]]:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        query = """
            SELECT i.*, p.name as provider_name 
            FROM items i 
            LEFT JOIN providers p ON i.provider_id = p.id
            WHERE i.active = 1 
            ORDER BY i.id DESC LIMIT ?
        """
        cur.execute(query, (limit,))
        return [dict(row) for row in cur.fetchall()]

def get_item_by_id(item_id: int) -> Optional[Dict[str, Any]]:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        query = """
            SELECT i.*, p.name as provider_name 
            FROM items i 
            LEFT JOIN providers p ON i.provider_id = p.id
            WHERE i.id = ?
        """
        cur.execute(query, (item_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def delete_item_by_sku(sku: str) -> bool:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE items SET active = 0 WHERE sku = ?", (sku,))
        conn.commit()
        return cur.rowcount > 0

def register_sale(title: str, client_id: Optional[int], items_list: List[Dict], payment_method: str) -> int:
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with closing(get_db_connection()) as conn:
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")
            
            total_sale = sum(item['qty'] * item['price'] for item in items_list)
            
            cur.execute("""
                INSERT INTO sales (title, client_id, total, payment_method, created_at) 
                VALUES (?, ?, ?, ?, ?)
            """, (title, client_id, total_sale, payment_method, created_at))
            
            sale_id = cur.lastrowid
            
            for item in items_list:
                cur.execute("UPDATE items SET stock = stock - ? WHERE id = ?", (item['qty'], item['id']))
                
                item_name = item.get('name', 'Producto Desconocido')
                
                cur.execute("""
                    INSERT INTO sale_items (sale_id, item_id, item_name, qty, unit_price) 
                    VALUES (?, ?, ?, ?, ?)
                """, (sale_id, item['id'], item_name, item['qty'], item['price']))
            
            conn.commit()
            return sale_id
        except Exception as e:
            conn.rollback()
            raise e

def get_all_sales(limit: int = 1000) -> List[Dict[str, Any]]:
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        query = """
            SELECT id, title, client_id, total, payment_method, created_at 
            FROM sales 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        cur.execute(query, (limit,))
        return [dict(row) for row in cur.fetchall()]

def get_sale_details(sale_id: int) -> List[Dict[str, Any]]:
    query = """
        SELECT 
            si.item_name,       
            si.qty, 
            si.unit_price, 
            (si.qty * si.unit_price) as subtotal, 
            i.sku               
        FROM sale_items si 
        LEFT JOIN items i ON si.item_id = i.id 
        WHERE si.sale_id = ?
    """
    with closing(get_db_connection()) as conn:
        cur = conn.cursor()
        cur.execute(query, (sale_id,))
        return [dict(row) for row in cur.fetchall()]

if __name__ == "__main__":
    init_db()