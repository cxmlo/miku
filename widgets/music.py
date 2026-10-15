from PyQt6.QtWidgets import QWidget, QLabel, QProgressBar, QApplication, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QRect, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath, QColor, QFont
import time
import os
import json
import uuid
import webbrowser

import music_controller

def save_favorite_song(title, artist):
    mem_path = os.path.join(os.path.dirname(__file__), "brain", "music_memory.json")
    os.makedirs(os.path.dirname(mem_path), exist_ok=True)
    
    favorites = []
    if os.path.exists(mem_path):
        try:
            with open(mem_path, "r", encoding="utf-8") as f:
                favorites = json.load(f)
        except: pass
        
    if any(f.get("title") == title and f.get("artist") == artist for f in favorites):
        favorites = [f for f in favorites if not (f.get("title") == title and f.get("artist") == artist)]
        with open(mem_path, "w", encoding="utf-8") as f:
            json.dump(favorites, f, indent=4, ensure_ascii=False)
        return "removed"
        
    favorites.append({
        "id": str(uuid.uuid4()),
        "title": title,
        "artist": artist,
        "timestamp": time.time(),
        "context": f"Al usuario le gusta la canción '{title}' de '{artist}'."
    })
    
    with open(mem_path, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=4, ensure_ascii=False)
    return "saved"

class ClickableIcon(QLabel):
    clicked = pyqtSignal()
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_icon()
        
    def load(self, path):
        self.path = path
        self.update_icon()
        
    def update_icon(self):
        if self.path and self.width() > 0:
            pixmap = QPixmap(self.path)
            if not pixmap.isNull():
                self.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                
    def resizeEvent(self, event):
        self.update_icon()
        super().resizeEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()

class MarqueeLabel(QLabel):
    def __init__(self, text="", font_size=12, bold=True, parent=None):
        super().__init__(parent)
        self.px = 0
        self._text = text
        
        font = QFont("Segoe UI", font_size)
        font.setBold(bold)
        self.setFont(font)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scroll)
        self.timer.start(50)
        
    def setText(self, text):
        if self._text != text:
            self._text = text
            self.px = 0
            self.update()
            
    def text(self):
        return self._text
            
    def update_scroll(self):
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(self._text)
        if w > self.width():
            self.px -= 1
            if self.px < -(w + 30):
                self.px = 0
            self.update()
        else:
            if self.px != 0:
                self.px = 0
                self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(QColor("white"))
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(self._text)
        
        y = (self.height() + fm.ascent() - fm.descent()) // 2
        
        if w > self.width():
            painter.drawText(self.px, y, self._text)
            painter.drawText(self.px + w + 30, y, self._text)
        else:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._text)


class MusicWidget(QWidget):
    def __init__(self, miku_parent=None):
        super().__init__(None)
        self.miku_parent = miku_parent
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.mode = 1 
        self.is_playing_state = False
        self.original_pixmap = None
        self.raw_bg_pixmap = None
        
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_media)
        self.timer.start(100) 
        
        self.last_session_id = ""
        self.is_showing = False
        self.is_pinned = False
        self.is_dragging = False
        self.anim_group = QParallelAnimationGroup(self)
        
        self.apply_mode(self.mode)

    def init_ui(self):
        # Cover for Mode 0
        self.cover_label = QLabel(self)
        self.cover_label.setStyleSheet("background-color: transparent;")
        
        self.title_label = MarqueeLabel(font_size=16, bold=True, parent=self)
        self.artist_label = MarqueeLabel(font_size=10, bold=False, parent=self)
        
        self.time_current = QLabel("0:00", self)
        self.time_current.setStyleSheet("color: white; font-size: 11px; font-weight: bold; font-family: 'Segoe UI';")
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.4);
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: white;
                border-radius: 3px;
            }
        """)
        
        self.time_total = QLabel("0:00", self)
        self.time_total.setStyleSheet("color: white; font-size: 11px; font-weight: bold; font-family: 'Segoe UI';")
        
        # Interactive Icons that preserve Aspect Ratio natively
        self.btn_heart = ClickableIcon("assets/music/heart.svg", self)
        self.btn_heart.clicked.connect(self.on_heart_clicked)
        
        self.btn_prev = ClickableIcon("assets/music/prev.svg", self)
        self.btn_prev.clicked.connect(self.on_prev_clicked)
        
        self.btn_play = ClickableIcon("assets/music/play.svg", self)
        self.btn_play.clicked.connect(self.on_play_clicked)
        
        self.btn_next = ClickableIcon("assets/music/next.svg", self)
        self.btn_next.clicked.connect(self.on_next_clicked)
        
        # Botones Mac
        self.btn_mac_close = QPushButton(self)
        self.btn_mac_min = QPushButton(self)
        self.btn_mac_open = QPushButton(self)
        
        mac_style = "QPushButton { border-radius: 7px; border: none; background-color: %s; } QPushButton:hover { border: 1px solid rgba(0,0,0,0.5); }"
        self.btn_mac_close.setStyleSheet(mac_style % "#FF605C") # Rojo
        self.btn_mac_min.setStyleSheet(mac_style % "#FFBD44")   # Amarillo
        self.btn_mac_open.setStyleSheet(mac_style % "#00CA4E")  # Verde
        
        for btn in (self.btn_mac_close, self.btn_mac_min, self.btn_mac_open):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
        self.btn_mac_close.clicked.connect(self.on_minimize_clicked)
        self.btn_mac_min.clicked.connect(self.toggle_mode)
        self.btn_mac_open.clicked.connect(self.open_spotify)

    def on_minimize_clicked(self):
        self.hide()
        self.is_showing = False
        self.user_closed = True
        
    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.reposition()
                
    def toggle_mode(self):
        if self.mode == 0:
            self.apply_mode(1)
            if self.is_pinned:
                self.is_pinned = False
        elif self.mode == 1:
            self.apply_mode(0)
        if not self.is_pinned:
            self.reposition()

    def open_spotify(self):
        import webbrowser
        webbrowser.open("spotify:")

    def on_heart_clicked(self):
        state = music_controller.media_state
        if state["title"] and state["artist"]:
            status = save_favorite_song(state["title"], state["artist"])
            if status == "saved":
                try:
                    self.btn_heart.load("assets/music/heart_filled.svg")
                except: pass
                from ui import ui_comm
                ui_comm.text_input_signal.emit(f"[SISTEMA] El usuario acaba de guardar en favoritos la canción '{state['title']}' de '{state['artist']}'. Dile algo lindo muy cortito.")
            elif status == "removed":
                try:
                    self.btn_heart.load("assets/music/heart.svg")
                except: pass

    def on_prev_clicked(self):
        music_controller.prev_track()

    def on_play_clicked(self):
        music_controller.toggle_play_pause()

    def on_next_clicked(self):
        music_controller.next_track()

    def apply_mode(self, mode):
        self.mode = mode
        
        if mode == 0:
            # Large Square (300x370) con altura extendida para un espaciado perfecto
            self.setFixedSize(300, 370)
            
            mac_style = "QPushButton { border-radius: 7px; border: none; background-color: %s; } QPushButton:hover { border: 1px solid rgba(0,0,0,0.5); }"
            self.btn_mac_close.setStyleSheet(mac_style % "#FF605C")
            if self.is_pinned:
                self.btn_mac_min.setStyleSheet(mac_style % "#FFBD44" + "QPushButton { border: 2px solid white; }")
            else:
                self.btn_mac_min.setStyleSheet(mac_style % "#FFBD44")
            self.btn_mac_open.setStyleSheet(mac_style % "#00CA4E")
            
            self.btn_mac_close.setGeometry(235, 12, 14, 14)
            self.btn_mac_min.setGeometry(255, 12, 14, 14)
            self.btn_mac_open.setGeometry(275, 12, 14, 14)
            self.btn_mac_close.show()
            self.btn_mac_min.show()
            self.btn_mac_open.show()
            
            # Corazón y carátula
            self.btn_heart.setGeometry(265, 50, 20, 20)
            self.btn_heart.show()
            
            self.cover_label.setGeometry(85, 65, 130, 130)
            self.cover_label.show()
            
            # Textos con 20px de separación de la carátula
            self.title_label.setGeometry(20, 215, 260, 25)
            self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            self.title_label.show()
            
            self.artist_label.setGeometry(20, 245, 260, 15)
            self.artist_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.artist_label.show()
            
            # Progreso
            self.progress_bar.setGeometry(30, 285, 240, 6)
            self.progress_bar.show()
            
            self.time_current.setGeometry(30, 295, 40, 15)
            self.time_current.show()
            
            self.time_total.setGeometry(230, 295, 40, 15)
            self.time_total.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.time_total.show()
            
            # Botones de reproducción
            self.btn_prev.setGeometry(90, 325, 20, 20)
            self.btn_play.setGeometry(140, 320, 30, 30)
            self.btn_next.setGeometry(200, 325, 20, 20)
            self.btn_prev.show()
            self.btn_play.show()
            self.btn_next.show()
            
        elif mode == 1:
            # Small Pill total size (250x120) to fit backplate shadow
            self.setFixedSize(250, 120)
            
            # Pequeños 10x10 con separación extra y border radius de 5
            mac_style = "QPushButton { border-radius: 5px; border: none; background-color: %s; } QPushButton:hover { border: 1px solid rgba(0,0,0,0.5); }"
            self.btn_mac_close.setStyleSheet(mac_style % "#FF605C")
            self.btn_mac_min.setStyleSheet(mac_style % "#FFBD44")
            self.btn_mac_open.setStyleSheet(mac_style % "#00CA4E")
            
            # Vertical buttons on the right backplate (Green, Yellow, Red)
            self.btn_mac_open.setGeometry(235, 25, 10, 10) # Green
            self.btn_mac_min.setGeometry(235, 45, 10, 10)  # Yellow
            self.btn_mac_close.setGeometry(235, 65, 10, 10) # Red
            self.btn_mac_close.show()
            self.btn_mac_min.show()
            self.btn_mac_open.show()
            
            self.btn_heart.setGeometry(195, 12, 18, 18) 
            self.btn_heart.show()
            
            self.cover_label.hide()
            
            self.title_label.setGeometry(20, 15, 165, 25) # Limita antes del corazon
            self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.title_label.show()
            
            self.artist_label.setGeometry(20, 40, 165, 15)
            self.artist_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            self.artist_label.show()
            
            self.progress_bar.setGeometry(20, 60, 190, 4)
            self.progress_bar.show()
            
            self.time_current.setGeometry(20, 68, 40, 15)
            self.time_current.show()
            
            self.time_total.setGeometry(170, 68, 40, 15)
            self.time_total.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.time_total.show()
            
            # Botones
            self.btn_prev.setGeometry(75, 82, 16, 16)
            self.btn_play.setGeometry(105, 78, 20, 20)
            self.btn_next.setGeometry(135, 82, 16, 16)
            self.btn_prev.show()
            self.btn_play.show()
            self.btn_next.show()
            
        elif mode == 2:
            # Icon Mode
            self.setFixedSize(50, 50)
            self.btn_heart.hide()
            self.cover_label.hide()
            self.title_label.hide()
            self.artist_label.hide()
            self.progress_bar.hide()
            self.time_current.hide()
            self.time_total.hide()
            self.btn_prev.hide()
            self.btn_play.hide()
            self.btn_next.hide()
            self.btn_mac_close.hide()
            self.btn_mac_min.hide()
            self.btn_mac_open.hide()

        self.reposition()
        self.update_backgrounds()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        radius = 25 if self.mode == 2 else 20
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        
        painter.setClipPath(path)
        
        if self.mode == 0:
            # Fondo base sólido del widget por defecto
            base_path = QPainterPath()
            base_path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.fillPath(base_path, QColor(25, 25, 25, 255))
            
            # Recuadro interior para la carátula o color de fondo
            inner_path = QPainterPath()
            inner_path.addRoundedRect(5, 40, self.width() - 10, self.height() - 45, 15, 15)
            
            if self.raw_bg_pixmap:
                painter.save()
                painter.setClipPath(inner_path)
                x_off = (self.width() - self.raw_bg_pixmap.width()) // 2
                y_off = (self.height() - self.raw_bg_pixmap.height()) // 2
                painter.drawPixmap(x_off, y_off, self.raw_bg_pixmap)
                painter.fillPath(inner_path, QColor(15, 15, 15, 235))
                painter.restore()
            else:
                painter.fillPath(inner_path, QColor(25, 25, 25, 220))
            
        elif self.mode == 1:
            # Fondo base sólido del widget por defecto
            back_path = QPainterPath()
            back_path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.fillPath(back_path, QColor(25, 25, 25, 255))
            
            # Tarjeta principal encima, desplazada para crear el borde asimétrico
            main_path = QPainterPath()
            # Borde de 5px arriba, abajo, izquierda, y un borde grueso de 25px a la derecha
            main_path.addRoundedRect(5, 5, self.width() - 30, self.height() - 10, 15, 15)
            
            if self.raw_bg_pixmap:
                painter.save()
                painter.setClipPath(main_path)
                x_off = (self.width() - self.raw_bg_pixmap.width()) // 2
                y_off = (self.height() - self.raw_bg_pixmap.height()) // 2
                painter.drawPixmap(x_off, y_off, self.raw_bg_pixmap)
                # Overlay oscuro para que el texto sea legible
                painter.fillPath(main_path, QColor(15, 15, 15, 210))
                painter.restore()
            else:
                painter.fillPath(main_path, QColor(25, 25, 25, 255))
                
        if self.mode == 2:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 16))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🎵")

    def format_time(self, seconds):
        if not seconds or seconds < 0:
            return "0:00"
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"

    def animate_to_pos(self, target_x, target_y):
        self.anim_group.clear()
        
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.setStartValue(self.geometry())
        
        anim.setEndValue(QRect(target_x, target_y, self.width(), self.height()))
        
        self.anim_group.addAnimation(anim)
        self.anim_group.start()

    def reposition(self):
        if hasattr(self, 'miku_parent') and hasattr(self.miku_parent, 'update_all_widgets_layout'):
            self.miku_parent.update_all_widgets_layout()

    def mousePressEvent(self, event):
        if self.mode == 1:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            if not self.is_pinned:
                self.toggle_pin()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.mode == 1:
            return
        if getattr(self, 'is_dragging', False) and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - getattr(self, 'drag_position', event.globalPosition().toPoint()))
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            event.accept()

    def set_miku_scale(self, scale_factor):
        if scale_factor == 0.5:
            if self.mode != 0:
                self.apply_mode(0)
                if not self.is_pinned:
                    self.reposition()
        else:
            if self.mode == 0:
                self.apply_mode(1)
                if self.is_pinned:
                    self.is_pinned = False
                    self.btn_mac_min.setStyleSheet("QPushButton { border-radius: 7px; border: none; background-color: #FFBD44; }")
                self.reposition()

    def update_backgrounds(self, pixmap=None):
        if pixmap is not None:
            self.original_pixmap = pixmap
            
        if not self.original_pixmap or self.original_pixmap.isNull():
            self.raw_bg_pixmap = None
            return
            
        # Escalar la imagen usando el tamaño ACTUAL del widget
        self.raw_bg_pixmap = self.original_pixmap.scaled(
            self.width(), self.height(), 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
            Qt.TransformationMode.SmoothTransformation
        )

    def poll_media(self):
        state = music_controller.media_state
        
        if not state["is_playing"] and not state["has_session"]:
            if self.is_showing:
                self.hide()
                self.is_showing = False
            return
            
        # Mostramos la UI si estaba oculta
        if not self.is_showing and not getattr(self, 'user_closed', False):
            self.show()
            self.is_showing = True
            self.reposition()
            
        # Si la canción cambió, reiniciamos el flag de user_closed para que vuelva a aparecer
        if state["session_id"] != self.last_session_id or state["title"] != self.title_label.text():
            self.user_closed = False
            
        if state["is_playing"]:
            if not self.is_playing_state:
                try: self.btn_play.load("assets/music/pause.svg")
                except: pass
                self.is_playing_state = True
        else:
            if self.is_playing_state:
                try: self.btn_play.load("assets/music/play.svg")
                except: pass
                self.is_playing_state = False

        if state["session_id"] != self.last_session_id or state["title"] != self.title_label.text():
            self.last_session_id = state["session_id"]
            self.title_label.setText(state["title"])
            self.artist_label.setText(state["artist"])
            
            saved = False
            mem_path = os.path.join(os.path.dirname(__file__), "brain", "music_memory.json")
            if os.path.exists(mem_path):
                try:
                    with open(mem_path, "r", encoding="utf-8") as f:
                        favorites = json.load(f)
                    saved = any(f.get("title") == state["title"] and f.get("artist") == state["artist"] for f in favorites)
                except: pass
                
            if saved:
                try: self.btn_heart.load("assets/music/heart_filled.svg")
                except: pass
            else:
                try: self.btn_heart.load("assets/music/heart.svg")
                except: pass
            
            if state["thumbnail_bytes"]:
                image = QImage()
                image.loadFromData(state["thumbnail_bytes"])
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    self.update_backgrounds(pixmap)
                    
                    scaled = pixmap.scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    target = QPixmap(130, 130)
                    target.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(target)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    path = QPainterPath()
                    path.addRoundedRect(0, 0, 130, 130, 10, 10)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, scaled)
                    painter.end()
                    self.cover_label.setPixmap(target)
            else:
                self.cover_label.clear()
                self.raw_bg_pixmap = None
                
            self.update() # FORZAR REPAINT CUANDO CAMBIA LA CANCION
                
        pos = state["position_sec"]
        end = state["end_time_sec"]
        
        if state["is_playing"] and state["last_update_time"] > 0:
            elapsed = time.time() - state["last_update_time"]
            pos += elapsed
            
        if pos > end: pos = end
        
        self.time_current.setText(self.format_time(pos))
        self.time_total.setText(self.format_time(end))
        
        if end > 0:
            self.progress_bar.setMaximum(int(end * 10))
            self.progress_bar.setValue(int(pos * 10))
        else:
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
        
        if self.mode != 0:
            self.reposition()
