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

class ClockWidget(NotificationBase):
    def __init__(self, miku_parent=None, parent=None):
        super().__init__(miku_parent, parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 40, 5, 5)
        
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setFixedWidth(320)
        self.container.setStyleSheet('''
            QWidget#MainContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                border-radius: 25px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
        ''')
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(25, 25, 25, 20)
        self.container_layout.setSpacing(10)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: rgba(255, 255, 255, 170); font-family: '-apple-system', 'Segoe UI', Arial; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.hide()
        
        self.clock_svg = QSvgWidget()
        self.clock_svg.setFixedSize(140, 140)
        
        self.clock_layout = QHBoxLayout()
        self.clock_layout.addStretch()
        self.clock_layout.addWidget(self.clock_svg)
        self.clock_layout.addStretch()
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 45px; font-weight: 700; background: transparent; border: none;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.container_layout.addWidget(self.title_label)
        self.container_layout.addLayout(self.clock_layout)
        self.container_layout.addWidget(self.time_label)
        
        self.layout.addWidget(self.container)
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_clock)
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.svg_base_path = os.path.join(project_root, "assets", "widget", "reloj", "rerloj.svg")

    def apply_mode(self, mode):
        super().apply_mode(mode)
        if mode == 1:
            self.clock_svg.hide()
            self.setFixedSize(250, 120)
            self.container.setFixedSize(215, 110)
            self.layout.setContentsMargins(5, 5, 30, 5)
            self.container.setStyleSheet('''
                QWidget#MainContainer {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                    border-radius: 15px;
                }
            ''')
            self.container_layout.setContentsMargins(15, 15, 15, 15)
            self.time_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 35px; font-weight: 700; background: transparent; border: none;")
        else:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            self.container.setMinimumSize(0, 0)
            self.container.setMaximumSize(16777215, 16777215)
            self.setFixedSize(QSize(300, 340)) # approx size
            self.container.setFixedSize(290, 295)
            self.layout.setContentsMargins(5, 40, 5, 5)
            self.container.setStyleSheet('''
                QWidget#MainContainer {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(60, 60, 60, 230), stop:1 rgba(30, 30, 30, 250));
                    border-radius: 25px;
                    border: 1px solid rgba(255, 255, 255, 60);
                }
            ''')
            self.container_layout.setContentsMargins(25, 25, 25, 20)
            self.clock_svg.show()
            self.time_label.setStyleSheet("color: white; font-family: '-apple-system', 'Segoe UI', Arial; font-size: 32px; font-weight: 700; background: transparent; border: none;")

    def show_clock(self, title, digital_time):
        self.title_label.hide() # title hidden per user request
        self.time_label.setText(digital_time)
        
        self.update_clock()
        self.update_timer.start(10000)
        
        self.show_animated(20000)

    def update_clock(self):
        try:
            with open(self.svg_base_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
                
            now = datetime.datetime.now()
            h = now.hour % 12
            m = now.minute
            
            minute_angle = (m / 60) * 360
            hour_angle = (h / 12) * 360 + (m / 60) * 30
            
            svg_content = svg_content.replace(
                '<rect class="fil6"', 
                f'<rect class="fil6" transform="rotate({minute_angle} 10795 13970)"'
            )
            # Fix viewBox and size to fit perfectly
            svg_content = svg_content.replace('viewBox="0 0 21590 27940"', 'viewBox="1748 4923 18094 18094"')
            import re
            svg_content = re.sub(r'width="[^"]+" height="[^"]+"', 'width="100%" height="100%"', svg_content, count=1)
            
            svg_content = svg_content.replace(
                '<rect class="fil7"', 
                f'<rect class="fil7" transform="rotate({hour_angle} 10795 13970)"'
            )
            
            self.clock_svg.load(bytearray(svg_content, encoding='utf-8'))
            
            time_str = now.strftime("%I:%M %p")
            self.time_label.setText(time_str)
        except Exception as e:
            print("Error loading clock SVG:", e)

    def schedule_hide(self, delay_seconds):
        if not self.is_pinned and self.isVisible():
            self.hide_timer.start((delay_seconds + 10) * 1000)

