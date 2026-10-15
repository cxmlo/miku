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

class UniversalCardWidget(NotificationBase):
    def __init__(self, miku_parent=None, parent=None):
        super().__init__(miku_parent, parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 40, 5, 5)
        
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QWidget#MainContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 50);
            }
        """)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(25, 20, 25, 20)
        self.container_layout.setSpacing(15)
        
        # Text area
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(5)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: rgba(255, 255, 255, 180); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.content_label = QLabel()
        self.content_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 18px; font-weight: 600; background: transparent; border: none;")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.content_label.setWordWrap(True)
        
        self.text_layout.addWidget(self.title_label)
        self.text_layout.addWidget(self.content_label)
        self.container_layout.addLayout(self.text_layout)
        
        # Grid for files
        self.files_grid_widget = QWidget()
        self.files_grid_widget.setStyleSheet("background: transparent; border: none;")
        self.files_grid = QGridLayout(self.files_grid_widget)
        self.files_grid.setSpacing(10)
        self.files_grid.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addWidget(self.files_grid_widget)
        
        self.layout.addWidget(self.container)
        self.has_files = False

    def apply_mode(self, mode):
        super().apply_mode(mode)
        if mode == 1:
            self.setFixedSize(250, 120)
            self.container.setFixedSize(215, 110)
            self.layout.setContentsMargins(5, 5, 30, 5)
            self.container.setStyleSheet("""
                QWidget#MainContainer {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                    border-radius: 15px;
                }
            """)
            self.container_layout.setContentsMargins(15, 15, 15, 15)
            self.files_grid_widget.hide()
            self.title_label.setStyleSheet("color: rgba(255, 255, 255, 180); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            self.content_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 15px; font-weight: 600; background: transparent; border: none;")
            self.title_label.setWordWrap(False)
            self.content_label.setWordWrap(False)
        else:
            self.setFixedWidth(300)
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.container.setFixedWidth(290)
            self.container.setMinimumHeight(0)
            self.container.setMaximumHeight(16777215)
            self.layout.setContentsMargins(5, 40, 5, 5)
            self.container.setStyleSheet("""
                QWidget#MainContainer {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 50);
                }
            """)
            self.container_layout.setContentsMargins(25, 20, 25, 20)
            if self.has_files:
                self.files_grid_widget.show()
            self.title_label.setStyleSheet("color: rgba(255, 255, 255, 180); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 14px; font-weight: 600; background: transparent; border: none;")
            self.content_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 18px; font-weight: 600; background: transparent; border: none;")
            self.title_label.setWordWrap(True)
            self.content_label.setWordWrap(True)
            self.adjustSize()

    def show_card(self, title, message, files=[]):
        self.title_label.setText(title)
        self.content_label.setText(message)
        
        if message.strip() == "":
            self.apply_mode(1)
        else:
            self.apply_mode(0)
            
        self.show_animated(20000)
        
        if not title:
            self.title_label.hide()
        else:
            self.title_label.show()
            
        if not message:
            self.content_label.hide()
        else:
            self.content_label.show()
            
        # Clear previous grid
        while self.files_grid.count():
            item = self.files_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        if files:
            self.has_files = True
            if self.mode == 0:
                self.files_grid_widget.show()
            max_cols = 3
            for i, f_path in enumerate(files):
                if i >= 6: # limit to 6 max items
                    break
                row = i // max_cols
                col = i % max_cols
                
                item_widget = FileItemWidget(f_path)
                item_widget.setFixedWidth(120)
                item_widget.setStyleSheet("""
                    QWidget {
                        background: rgba(0, 0, 0, 80);
                        border-radius: 10px;
                    }
                """)
                item_layout = QVBoxLayout(item_widget)
                item_layout.setContentsMargins(10, 10, 10, 10)
                item_layout.setSpacing(5)
                
                preview_label = QLabel()
                preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                preview_label.setFixedSize(80, 80)
                preview_label.setStyleSheet("background: transparent;")
                
                base_name = os.path.basename(f_path)
                if len(base_name) > 17:
                    name, ext = os.path.splitext(base_name)
                    if len(name) > 11:
                        name = name[:10] + ".."
                    base_name = name + ext
                
                name_label = QLabel(base_name)
                name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                name_label.setStyleSheet("color: #ccc; font-size: 11px; font-weight: 500; background: transparent;")
                
                # Try to load image
                if str(f_path).lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')):
                    pixmap = QPixmap(f_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        preview_label.setPixmap(pixmap)
                    else:
                        ext = os.path.splitext(f_path)[1].upper().replace('.', '')
                        preview_label.setText(f"[{ext}]")
                        preview_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #aaa; background: transparent;")
                else:
                    ext = os.path.splitext(f_path)[1].upper().replace('.', '')
                    preview_label.setText(f"[{ext}]")
                    preview_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #aaa; background: transparent;")
                    
                item_layout.addWidget(preview_label)
                item_layout.addWidget(name_label)
                self.files_grid.addWidget(item_widget, row, col)
        else:
            self.has_files = False
            self.files_grid_widget.hide()
            
        delay = 15 if files else 8
        self.show_animated(delay * 1000)

class FileItemWidget(QWidget):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            import os
            try:
                os.startfile(self.file_path)
            except Exception as e:
                print(f"Error abriendo archivo: {e}")

