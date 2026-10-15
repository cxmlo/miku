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

class InfoWidget(NotificationBase):
    def __init__(self, miku_parent=None, parent=None):
        super().__init__(miku_parent, parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 40, 5, 5)
        
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QWidget#MainContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 220), stop:1 rgba(30, 30, 30, 240));
                border-radius: 25px;
                border: 1px solid rgba(255, 255, 255, 50);
            }
        """)
        
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(25, 20, 25, 20)
        self.container_layout.setSpacing(20)
        
        self.icon_stack = QStackedWidget()
        self.icon_stack.setFixedSize(60, 60)
        
        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("font-size: 50px; background: transparent; border: none;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_svg = QSvgWidget()
        self.icon_svg.setStyleSheet("background: transparent; border: none;")
        
        self.icon_stack.addWidget(self.icon_label)
        self.icon_stack.addWidget(self.icon_svg)
        
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(5)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: rgba(255, 255, 255, 180); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 15px; font-weight: 600; background: transparent; border: none;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.content_label = QLabel()
        self.content_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 20px; font-weight: 600; background: transparent; border: none;")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.content_label.setWordWrap(True)
        
        self.text_layout.addWidget(self.title_label)
        self.text_layout.addWidget(self.content_label)
        
        self.container_layout.addWidget(self.icon_stack)
        self.container_layout.addLayout(self.text_layout)
        
        self.layout.addWidget(self.container)

    def apply_mode(self, mode):
        super().apply_mode(mode)
        if mode == 1:
            self.setFixedSize(250, 120)
            self.container.setFixedSize(215, 110)
            self.layout.setContentsMargins(5, 5, 30, 5)
            self.container.setStyleSheet("""
                QWidget#MainContainer {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 220), stop:1 rgba(30, 30, 30, 240));
                    border-radius: 15px;
                }
            """)
            self.container_layout.setContentsMargins(15, 15, 15, 15)
            self.icon_stack.setFixedSize(40, 40)
            self.icon_label.setStyleSheet("font-size: 35px; background: transparent; border: none;")
            self.title_label.setStyleSheet("color: rgba(255, 255, 255, 180); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            self.content_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 15px; font-weight: 600; background: transparent; border: none;")
            
            # Limitar a que en modo pequeño se vea truncado o ajustado
            self.title_label.setWordWrap(False)
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
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 220), stop:1 rgba(30, 30, 30, 240));
                    border-radius: 25px;
                    border: 1px solid rgba(255, 255, 255, 50);
                }
            """)
            self.container_layout.setContentsMargins(25, 20, 25, 20)
            self.icon_stack.setFixedSize(60, 60)
            self.icon_label.setStyleSheet("font-size: 50px; background: transparent; border: none;")
            self.title_label.setStyleSheet("color: rgba(255, 255, 255, 180); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 15px; font-weight: 600; background: transparent; border: none;")
            self.content_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 20px; font-weight: 600; background: transparent; border: none;")
            
            self.title_label.setWordWrap(True)
            self.adjustSize()

    def show_info(self, title, content, duration, icon):
        if icon.startswith("SVG:"):
            svg_data = icon[4:].encode('utf-8')
            self.icon_svg.load(svg_data)
            self.icon_stack.setCurrentWidget(self.icon_svg)
        else:
            self.icon_label.setText(icon)
            self.icon_stack.setCurrentWidget(self.icon_label)
            
        self.title_label.setText(title)
        self.content_label.setText(content)
        
        self.show_animated(int(duration * 1000))

    def schedule_hide(self, delay_seconds):
        if not self.is_pinned and self.isVisible():
            self.hide_timer.start(delay_seconds * 1000)

