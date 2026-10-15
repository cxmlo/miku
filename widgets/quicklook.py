import os
import sys
import datetime
from PyQt6.QtWidgets import (QApplication, QLabel, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QWidget, QLineEdit, QComboBox, 
                             QGraphicsOpacityEffect, QStackedWidget, QPushButton, QGridLayout)
from PyQt6.QtGui import QMovie, QMouseEvent, QImageReader, QPainter, QPainterPath, QColor, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtSvgWidgets import QSvgWidget

from widgets.base import NotificationBase

class QuickLookWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)
        
        self.close_btn = QPushButton("✖")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 30, 30, 150);
                color: rgba(255, 255, 255, 200);
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid rgba(255, 255, 255, 50);
            }
            QPushButton:hover { 
                background-color: rgba(60, 60, 60, 200); 
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        self.close_btn.setParent(self)
        self.close_btn.hide()
        
        self.is_dragging = False
        self.drag_position = None
        
    def show_preview(self, file_path):
        is_pdf = str(file_path).lower().endswith('.pdf')
        is_gif = str(file_path).lower().endswith('.gif')
        is_img = str(file_path).lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))
        
        # Limpiar GIF anterior si existe
        if hasattr(self, 'movie') and self.movie:
            self.movie.stop()
            self.movie = None
            
        screen = QApplication.primaryScreen().geometry()
        max_w = int(screen.width() * 0.7)
        max_h = int(screen.height() * 0.7)
        
        if is_gif:
            from PyQt6.QtGui import QMovie
            from PyQt6.QtCore import QSize
            self.movie = QMovie(file_path)
            self.movie.jumpToFrame(0)
            orig_size = self.movie.currentImage().size()
            if not orig_size.isEmpty():
                scaled_size = orig_size.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio)
                self.movie.setScaledSize(scaled_size)
            
            self.image_label.setMovie(self.movie)
            self.movie.start()
            
            if not orig_size.isEmpty():
                self.resize(scaled_size)
            else:
                self.resize(400, 400)
                
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
            
            self.close_btn.move(self.width() - 40, 10)
            self.close_btn.show()
            self.close_btn.raise_()
            
            self.show()
            self.raise_()
            self.activateWindow()
            return
            
        pixmap = None
        if is_img:
            pixmap = QPixmap(file_path)
        elif is_pdf:
            try:
                import fitz
                from PyQt6.QtGui import QImage
                doc = fitz.open(file_path)
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
            except Exception as e:
                print(f"Error renderizando PDF: {e}")
                return
                
        if pixmap and not pixmap.isNull():
            pixmap = pixmap.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.resize(pixmap.size())
            
            # Center on screen
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
            
            self.close_btn.move(self.width() - 40, 10)
            self.close_btn.show()
            self.close_btn.raise_()
            
            self.show()
            self.raise_()
            self.activateWindow()
                
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            self.is_dragging = True
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            self.is_dragging = False
            event.accept()
            


    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.hide()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

