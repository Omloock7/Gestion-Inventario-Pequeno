# db.py - capa simple para sqlite3
import sqlite3
from contextlib import closing

DB_PATH = "motos_taller.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        # items: piezas, repuestos, etc.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT CHECK(LENGTH(description) <= 255),
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            provider_id INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        # clientes
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            notes TEXT CHECK(LENGTH(notes) <= 225),
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        # providers
        cur.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            notes TEXT CHECK(LENGTH(notes) <= 225),
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        # ventas (header)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            total REAL NOT NULL,
            payment_method TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        # items de venta  (detalle)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            unit_price REAL NOT NULL
        )""")
        conn.commit()

# CRUD básicos
def add_item(sku, name, description, price, stock, provider_id=None):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items (sku, name, description, price, stock, provider_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sku, name, description, price, stock, provider_id))
        conn.commit()
        return cur.lastrowid

def get_items(limit=100):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM items ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

def update_item_stock(item_id, new_stock):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE items SET stock = ? WHERE id = ?", (new_stock, item_id))
        conn.commit()
        return cur.rowcount

def get_item_by_id(item_id):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    
def get_item_by_sku(sku):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM items WHERE sku = ?", (sku,))
        row = cur.fetchone()
        return dict(row) if row else None


def delete_item_by_sku(sku):
    with closing(get_connection()) as conn:
        cur = conn.cursor()

        # comprobar si existe
        cur.execute("SELECT * FROM items WHERE sku = ?", (sku,))
        row = cur.fetchone()
        if not row:
            return 0

        # borrar
        cur.execute("DELETE FROM items WHERE sku = ?", (sku,))
        conn.commit()
        return cur.rowcount
