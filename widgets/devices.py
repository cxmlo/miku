import sys
import uuid
import socket
import qrcode
import requests
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QWidget)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
import miku_db

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class DevicesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dispositivos Vinculados")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-family: Arial;
            }
            QPushButton {
                background-color: #222222;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QListWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #333;
                border-radius: 5px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        
        # Header
        title = QLabel("Tus Dispositivos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(title)
        
        # List
        self.device_list = QListWidget()
        self.layout.addWidget(self.device_list)
        self.refresh_list()
        
        # Pair section
        self.pair_btn = QPushButton("Vincular nuevo dispositivo (QR)")
        self.pair_btn.clicked.connect(self.show_qr)
        self.layout.addWidget(self.pair_btn)
        
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.hide()
        self.layout.addWidget(self.qr_label)
        
        self.qr_info = QLabel("Escanea este código con la app de Miku.\nEl código expira en 60 segundos.")
        self.qr_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_info.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        self.qr_info.hide()
        self.layout.addWidget(self.qr_info)
        
        # Guardaremos la sesión actual por si necesitamos verificarla
        self.current_session = None

    def refresh_list(self):
        self.device_list.clear()
        devices = miku_db.get_all_devices()
        if not devices:
            self.device_list.addItem("No hay dispositivos vinculados.")
            return
            
        for dev in devices:
            item = QListWidgetItem(f"📱 {dev['name']} (Última vez: {dev['last_seen']})")
            # Podríamos añadir botones para eliminar, pero por ahora solo mostramos
            self.device_list.addItem(item)
            
    def show_qr(self):
        self.pair_btn.setEnabled(False)
        self.current_session = str(uuid.uuid4())
        # Usa el dominio de Cloudflare en lugar de IP local
        ip = "miku.temploarcangelesdelamor.com"
        
        qr_data = f"miku://pair?s={self.current_session}&ip={ip}"
        print(f"[AUTH] QR generado: {qr_data}")
        
        # Avisar al servidor
        try:
            requests.post("http://127.0.0.1:8000/api/pair/init", json={"session_id": self.current_session}, timeout=1)
        except:
            pass
            
        # Generar QR
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Crear imagen para PyQt
        img = qr.make_image(fill_color="black", back_color="white")
        # Convert PIL to QImage
        img = img.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qim = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qim)
        
        self.qr_label.setPixmap(pix)
        self.qr_label.show()
        self.qr_info.show()
        
        # Expirar QR en 60s
        QTimer.singleShot(60000, self.hide_qr)
        
    def hide_qr(self):
        self.qr_label.hide()
        self.qr_info.hide()
        self.pair_btn.setEnabled(True)
        self.current_session = None
