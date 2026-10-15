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

class WeatherWidget(NotificationBase):
    def __init__(self, miku_parent=None, parent=None):
        super().__init__(miku_parent, parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 40, 5, 5)
        
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QWidget#MainContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                border-radius: 25px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
        """)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(25, 25, 25, 20)
        self.container_layout.setSpacing(10)
        
        # --- Top row: Icon + Temp ---
        self.top_layout = QHBoxLayout()
        self.top_layout.setSpacing(15)
        
        self.icon_svg = QSvgWidget()
        self.icon_svg.setFixedSize(55, 55)
        self.icon_svg.setStyleSheet("background: transparent; border: none;")
        
        self.temp_label = QLabel()
        self.temp_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 35px; font-weight: 700; background: transparent; border: none;")
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.top_layout.addWidget(self.icon_svg)
        self.top_layout.addWidget(self.temp_label)
        self.top_layout.addStretch()
        
        # --- Middle: Location and Condition ---
        self.city_label = QLabel()
        self.city_label.setStyleSheet("color: rgba(255, 255, 255, 170); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        
        self.cond_label = QLabel()
        self.cond_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 16px; font-weight: 500; background: transparent; border: none;")
        self.cond_label.setWordWrap(True)
        
        # --- Bottom row: Wind and Humidity ---
        self.bottom_widget = QWidget()
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        self.bottom_layout.setContentsMargins(0,0,0,0)
        self.bottom_layout.setSpacing(8)
        
        self.wind_icon = QSvgWidget()
        self.wind_icon.setFixedSize(20, 20)
        self.wind_icon.setStyleSheet("background: transparent; border: none;")
        
        self.wind_label = QLabel()
        self.wind_label.setStyleSheet("color: rgba(255, 255, 255, 200); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 14px; font-weight: 500; background: transparent; border: none;")
        
        self.hum_icon = QLabel("💧")
        self.hum_icon.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        
        self.hum_label = QLabel()
        self.hum_label.setStyleSheet("color: rgba(255, 255, 255, 200); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 14px; font-weight: 500; background: transparent; border: none;")
        
        self.bottom_layout.addWidget(self.wind_icon)
        self.bottom_layout.addWidget(self.wind_label)
        self.bottom_layout.addSpacing(15)
        self.bottom_layout.addWidget(self.hum_icon)
        self.bottom_layout.addWidget(self.hum_label)
        self.bottom_layout.addStretch()
        
        # Assemble
        self.container_layout.addWidget(self.city_label)
        self.container_layout.addLayout(self.top_layout)
        self.container_layout.addWidget(self.cond_label)
        self.container_layout.addSpacing(5)
        self.container_layout.addWidget(self.bottom_widget)
        
        self.layout.addWidget(self.container)

    def apply_mode(self, mode):
        super().apply_mode(mode)
        if mode == 1:
            self.city_label.show()
            self.cond_label.hide()
            self.bottom_widget.hide()
            self.setFixedWidth(250)
            self.container.setFixedWidth(215)
            self.setMinimumHeight(120)
            self.container.setMinimumHeight(110)
            self.layout.setContentsMargins(5, 5, 30, 5)
            self.container.setStyleSheet("""
                QWidget#MainContainer {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                    border-radius: 15px;
                }
            """)
            self.container_layout.setContentsMargins(15, 15, 15, 15)
            self.icon_svg.setFixedSize(50, 50)
            self.temp_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 30px; font-weight: 700; background: transparent; border: none;")
        else:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            self.container.setMinimumSize(0, 0)
            self.container.setMaximumSize(16777215, 16777215)
            
            self.setFixedWidth(300)
            self.container.setFixedWidth(290)
            
            self.layout.setContentsMargins(5, 40, 5, 5)
            self.container.setStyleSheet("""
                QWidget#MainContainer {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                    border-radius: 25px;
                    border: 1px solid rgba(255, 255, 255, 60);
                }
            """)
            self.container_layout.setContentsMargins(25, 25, 25, 20)
            self.icon_svg.setFixedSize(55, 55)
            self.temp_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 35px; font-weight: 700; background: transparent; border: none;")
            self.city_label.show()
            self.cond_label.show()
            self.bottom_widget.show()

    def show_weather(self, title, temp, cond, wind, hum, svg_path):
        self.city_label.setText(title.upper())
        self.temp_label.setText(temp)
        self.cond_label.setText(cond)
        self.wind_label.setText(wind)
        self.hum_label.setText(hum)
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        wind_svg_path = os.path.join(project_root, "assets", "widget", "google-weather-icons-main", "other", "assets", "light", "wind_02.svg")
        self.wind_icon.load(wind_svg_path)

        
        self.show_animated(8000)

    def schedule_hide(self, delay_seconds):
        if not self.is_pinned and self.isVisible():
            self.hide_timer.start(delay_seconds * 1000)

