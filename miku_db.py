import sqlite3
import os
import datetime
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "miku_devices.db")
KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "miku_identity.json")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            public_key TEXT NOT NULL,
            linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_server_identity():
    """Obtiene o genera la identidad criptográfica del servidor Miku Desktop."""
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, 'r') as f:
            data = json.load(f)
            private_key_bytes = bytes.fromhex(data['private_key'])
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            public_key = private_key.public_key()
            return private_key, public_key
    else:
        # Generar nueva identidad
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Guardar en archivo (En producción esto iría al Credential Manager del OS)
        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(KEY_PATH, 'w') as f:
            json.dump({
                'private_key': priv_bytes.hex()
            }, f)
            
        # Intentar ocultar el archivo en Windows
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(KEY_PATH, FILE_ATTRIBUTE_HIDDEN)
        except:
            pass
            
        return private_key, public_key

def get_server_public_key_b64():
    _, pub = get_server_identity()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    import base64
    return base64.b64encode(pub_bytes).decode('utf-8')

def add_device(device_id, name, public_key_b64):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO devices (device_id, name, public_key, linked_at, last_seen)
        VALUES (?, ?, ?, ?, ?)
    ''', (device_id, name, public_key_b64, datetime.datetime.now(), datetime.datetime.now()))
    conn.commit()
    conn.close()

def get_device(device_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT device_id, name, public_key FROM devices WHERE device_id = ?', (device_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"device_id": row[0], "name": row[1], "public_key": row[2]}
    return None

def update_last_seen(device_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE devices SET last_seen = ? WHERE device_id = ?', (datetime.datetime.now(), device_id))
    conn.commit()
    conn.close()

def is_valid_device(device_id: str) -> bool:
    """Verifica si un dispositivo está registrado y autorizado."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT device_id FROM devices WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        return row is not None
    except Exception as e:
        print(f"[DB] Error validando dispositivo: {e}")
        return False
    finally:
        conn.close()

def remove_device(device_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM devices WHERE device_id = ?', (device_id,))
    conn.commit()
    conn.close()

def get_all_devices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT device_id, name, public_key, linked_at, last_seen FROM devices')
    rows = c.fetchall()
    conn.close()
    return [{"device_id": r[0], "name": r[1], "public_key": r[2], "linked_at": r[3], "last_seen": r[4]} for r in rows]

# Inicializar al importar
init_db()
get_server_identity()
