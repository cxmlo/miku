import os
import sys
import datetime
from PyQt6.QtWidgets import (QApplication, QLabel, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QWidget, QLineEdit, QComboBox, 
                             QGraphicsOpacityEffect, QStackedWidget, QPushButton, QGridLayout)
from PyQt6.QtGui import QMovie, QMouseEvent, QImageReader, QPainter, QPainterPath, QColor, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtSvgWidgets import QSvgWidget

class NotificationBase(QWidget):
    def __init__(self, miku_parent=None, parent=None):
        super().__init__(parent)
        self.miku_parent = miku_parent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        self.mode = 1 # 1: Small, 0: Large
        self.is_pinned = False
        self.is_dragging = False
        self.was_dragged_out = False
        self.last_shown_time = 0
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.finished.connect(self.on_animation_finished)
        
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_animated)
        
        self.btn_mac_close = QPushButton(self)
        self.btn_mac_min = QPushButton(self) 
        self.btn_mac_open = QPushButton(self)
        
        mac_style = "QPushButton { border-radius: 7px; border: none; background-color: %s; } QPushButton:hover { border: 1px solid rgba(0,0,0,0.5); }"
        self.btn_mac_close.setStyleSheet(mac_style % "#FF605C")
        self.btn_mac_min.setStyleSheet(mac_style % "#FFBD44")
        self.btn_mac_open.setStyleSheet(mac_style % "#00CA4E")
        
        for btn in (self.btn_mac_close, self.btn_mac_min, self.btn_mac_open):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
        self.btn_mac_close.clicked.connect(self.hide_animated)
        self.btn_mac_min.clicked.connect(self.toggle_pin)
        self.btn_mac_open.clicked.connect(self.toggle_mode)
        
    def setup_mac_buttons(self):
        if self.mode == 1:
            radius = 5
            x_pos = self.width() - 20
            self.btn_mac_open.setGeometry(x_pos, 25, 10, 10)
            self.btn_mac_min.setGeometry(x_pos, 45, 10, 10)
            self.btn_mac_close.setGeometry(x_pos, 65, 10, 10)
        else:
            radius = 7
            btn_w = 14
            x_start = self.width() - 65 
            self.btn_mac_close.setGeometry(x_start, 12, btn_w, btn_w)
            self.btn_mac_min.setGeometry(x_start + 20, 12, btn_w, btn_w)
            self.btn_mac_open.setGeometry(x_start + 40, 12, btn_w, btn_w)
            
        mac_style = f"QPushButton {{ border-radius: {radius}px; border: none; background-color: %s; }} QPushButton:hover {{ border: 1px solid rgba(0,0,0,0.5); }}"
        self.btn_mac_close.setStyleSheet(mac_style % "#FF605C")
        self.btn_mac_open.setStyleSheet(mac_style % "#00CA4E")
        if self.is_pinned:
            self.btn_mac_min.setStyleSheet(mac_style % "#FFBD44" + " QPushButton { border: 2px solid white; }")
        else:
            self.btn_mac_min.setStyleSheet(mac_style % "#FFBD44")
            
        self.btn_mac_close.raise_()
        self.btn_mac_min.raise_()
        self.btn_mac_open.raise_()
        self.btn_mac_close.show()
        self.btn_mac_min.show()
        self.btn_mac_open.show()
        
    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        radius = 5 if self.mode == 1 else 7
        if self.is_pinned:
            self.hide_timer.stop()
            self.btn_mac_min.setStyleSheet(f"QPushButton {{ border-radius: {radius}px; border: 2px solid white; background-color: #FFBD44; }}")
            if hasattr(self.miku_parent, 'update_all_widgets_layout'):
                self.miku_parent.update_all_widgets_layout()
        else:
            self.hide_timer.start(5000)
            self.btn_mac_min.setStyleSheet(f"QPushButton {{ border-radius: {radius}px; border: none; background-color: #FFBD44; }}")
            if hasattr(self.miku_parent, 'update_all_widgets_layout'):
                self.miku_parent.update_all_widgets_layout()
                
    def toggle_mode(self):
        self.apply_mode(0 if self.mode == 1 else 1)
        if hasattr(self.miku_parent, 'update_all_widgets_layout') and not self.is_pinned:
            self.miku_parent.update_all_widgets_layout()
        
    def apply_mode(self, mode):
        self.mode = mode
        self.setup_mac_buttons()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if getattr(self, 'is_dragging', False) and event.buttons() == Qt.MouseButton.LeftButton:
            self.was_dragged_out = True
            self.move(event.globalPosition().toPoint() - getattr(self, 'drag_position', event.globalPosition().toPoint()))
            event.accept()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setup_mac_buttons()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        back_path = QPainterPath()
        back_path.addRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        painter.fillPath(back_path, QColor(25, 25, 25, 255))
        super().paintEvent(event)
        
    def show_animated(self, duration=20000):
        import time
        self.last_shown_time = time.time()
        self.apply_mode(self.mode)
        self.show()
        if hasattr(self.miku_parent, 'update_all_widgets_layout'):
            self.miku_parent.update_all_widgets_layout()
            
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass
            
        self.animation.setDirection(QPropertyAnimation.Direction.Forward)
        self.animation.setStartValue(self.opacity_effect.opacity())
        self.animation.setEndValue(1.0)
        self.animation.start()
        if not self.is_pinned:
            self.hide_timer.start(duration)
            
    def hide_animated(self):
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass
            
        self.animation.finished.connect(self.hide)
        self.animation.setDirection(QPropertyAnimation.Direction.Backward)
        self.animation.setStartValue(self.opacity_effect.opacity())
        self.animation.setEndValue(0.0)
        self.animation.start()
        
    def on_animation_finished(self):
        if self.animation.direction() == QPropertyAnimation.Direction.Backward:
            self.hide()
            if hasattr(self.miku_parent, 'update_all_widgets_layout'):
                self.miku_parent.update_all_widgets_layout()

