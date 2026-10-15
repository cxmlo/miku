import sys
import os
import datetime
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QComboBox, QGraphicsOpacityEffect
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QComboBox, QGraphicsOpacityEffect, QStackedWidget, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QMovie, QMouseEvent, QImageReader, QPainter, QPainterPath, QColor, QAction, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtSvgWidgets import QSvgWidget
from widgets.music import MusicWidget
from widgets.weather import WeatherWidget
from widgets.clock import ClockWidget
from widgets.info import InfoWidget
from widgets.card import UniversalCardWidget
from widgets.quicklook import QuickLookWidget
from widgets.devices import DevicesDialog
import ctypes

class UIComm(QObject):
    change_state_signal = pyqtSignal(str)
    wake_signal = pyqtSignal()
    text_input_signal = pyqtSignal(str)
    change_mic_signal = pyqtSignal(int)
    agent_status_signal = pyqtSignal(str)
    show_info_signal = pyqtSignal(str, str, int, str)
    show_weather_signal = pyqtSignal(str, str, str, str, str, str) # title, temp, cond, wind, hum, svg_path
    show_clock_signal = pyqtSignal(str, str)
    hide_info_signal = pyqtSignal(int)
    show_card_signal = pyqtSignal(str, str, list) # title, message, list of file paths
    show_quicklook_signal = pyqtSignal(str)
    modify_widget_state_signal = pyqtSignal(str, str) # widget_name, action

ui_comm = UIComm()

from PyQt6.QtWidgets import QPushButton

from widgets.settings_dialog import SettingsDialog

class MikuFace(QMainWindow):
    def show_settings(self):
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def __init__(self, devices=[]):
        super().__init__()
        self.devices = devices
        self.settings_dialog = None
        self.setWindowTitle("Miku V2")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        self.agent_status_label = QLabel("")
        self.agent_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.agent_status_label.setStyleSheet("color: #00FF00; font-family: Consolas; font-size: 11px; background-color: rgba(0, 0, 0, 150); border-radius: 5px;")
        self.agent_status_label.hide() # Oculto por defecto
        self.layout.addWidget(self.agent_status_label)
        
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Añadir sombra paralela suave para que Miku sea visible sobre fondos blancos
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 0)
        self.label.setGraphicsEffect(shadow)
        
        self.layout.addWidget(self.label)
        
        # Dropdown para micrófonos
        self.mic_combo = QComboBox()
        self.mic_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.mic_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(20, 20, 20, 200);
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 4px;
                font-family: Arial;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #222;
                color: white;
                selection-background-color: #444;
            }
        """)
        
        self.mic_combo.addItem("Micrófono por defecto del sistema", userData=-1)
        wo_index = 0
        for i, (idx, name) in enumerate(devices):
            self.mic_combo.addItem(name, userData=idx)
            if "WO" in name or "wo mic" in name.lower():
                wo_index = i + 1
                
        if wo_index > 0:
            self.mic_combo.setCurrentIndex(wo_index)
            
        self.mic_combo.currentIndexChanged.connect(self.on_mic_changed)
        
        self.pair_btn = QPushButton("📱")
        self.pair_btn.setFixedSize(28, 28)
        self.pair_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(20, 20, 20, 200);
                color: white; border: 1px solid #555; border-radius: 5px; font-size: 14px;
            }
            QPushButton:hover { background-color: rgba(60, 60, 60, 200); }
        """)
        self.pair_btn.clicked.connect(self.open_devices_dialog)
        
        # Agrupar mic_combo y pair_btn
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0,0,0,0)
        controls_layout.addWidget(self.mic_combo)
        controls_layout.addWidget(self.pair_btn)
        
        self.layout.addLayout(controls_layout)
        
        self.inbox = QLineEdit()
        self.inbox.setPlaceholderText("Escribe o haz clic en Miku...")
        self.inbox.setStyleSheet("""
            QLineEdit {
                background-color: rgba(20, 20, 20, 200);
                color: white;
                border: 1px solid #555;
                border-radius: 10px;
                padding: 8px;
                font-family: Arial;
                font-size: 14px;
            }
        """)
        self.inbox.returnPressed.connect(self.on_text_entered)
        self.layout.addWidget(self.inbox)
        
        self.current_state = "idle"
        self.movie = None
        self.base_path = os.path.join("assets", "animations")
        self.scale_factor = 0.25 # Mini mode (Mascota Virtual) por defecto
        
        # Ocultar controles por defecto
        self.inbox.hide()
        self.mic_combo.hide()
        self.pair_btn.hide()
        
        self.drag_position = None
        self.is_dragging = False
        
        self.single_click_timer = QTimer(self)
        self.single_click_timer.setSingleShot(True)
        self.single_click_timer.timeout.connect(self.trigger_assistant_action)
        
        ui_comm.change_state_signal.connect(self.change_state)
        ui_comm.agent_status_signal.connect(self.update_agent_status)
        
        self.info_widget = InfoWidget(miku_parent=self)
        self.universal_card = UniversalCardWidget(miku_parent=self)
        self.quicklook = QuickLookWidget()
        ui_comm.show_quicklook_signal.connect(self.handle_quicklook)
        self.weather_widget = WeatherWidget(miku_parent=self)
        self.music_widget = MusicWidget(self)
        self.clock_widget = ClockWidget(miku_parent=self)
        self.setAcceptDrops(True)
        ui_comm.show_info_signal.connect(self.info_widget.show_info)
        ui_comm.hide_info_signal.connect(self.info_widget.schedule_hide)
        ui_comm.show_card_signal.connect(self.universal_card.show_card)
        ui_comm.show_weather_signal.connect(self.weather_widget.show_weather)
        ui_comm.hide_info_signal.connect(self.weather_widget.schedule_hide)
        ui_comm.show_clock_signal.connect(self.clock_widget.show_clock)
        ui_comm.hide_info_signal.connect(self.clock_widget.schedule_hide)
        ui_comm.modify_widget_state_signal.connect(self.on_modify_widget_state)
        
        self.play_gif("sleeping-part2.gif", loop=True)
        
    def open_devices_dialog(self):
        dialog = DevicesDialog(self)
        dialog.exec()
        
    def on_modify_widget_state(self, widget_name, action):
        target = None
        if widget_name == "clima": target = getattr(self, 'weather_widget', None)
        elif widget_name == "reloj": target = getattr(self, 'clock_widget', None)
        elif widget_name == "musica": target = getattr(self, 'music_widget', None)
        elif widget_name == "info": target = getattr(self, 'info_widget', None)
        elif widget_name == "tarjeta": target = getattr(self, 'universal_card', None)
        
        if not target or not target.isVisible(): return
        
        if action == "fijar" and not getattr(target, 'is_pinned', False):
            if hasattr(target, 'toggle_pin'): target.toggle_pin()
        elif action == "desfijar" and getattr(target, 'is_pinned', False):
            if hasattr(target, 'toggle_pin'): target.toggle_pin()
        elif action == "maximizar" and getattr(target, 'mode', 0) == 1:
            if hasattr(target, 'toggle_mode'): target.toggle_mode()
        elif action == "minimizar" and getattr(target, 'mode', 1) == 0:
            if hasattr(target, 'toggle_mode'): target.toggle_mode()
        elif action == "cerrar":
            if hasattr(target, 'hide_animated'): target.hide_animated()
            elif hasattr(target, 'hide'): target.hide()

    def handle_quicklook(self, file_path):
        import os
        try:
            pipes = [p for p in os.listdir(r'\\.\pipe') if 'QuickLook.App.Pipe.' in p]
            if pipes:
                pipe_name = r'\\.\pipe\\' + pipes[0]
                msg = f"QuickLook.App.PipeMessages.Toggle|{os.path.abspath(file_path)}".encode('utf-8')
                with open(pipe_name, 'wb') as f:
                    f.write(msg)
                return
        except Exception as e:
            print(f"Fallo al invocar QuickLook original: {e}")
            
        # Fallback al QuickLook interno si el original no está
        self.quicklook.show_preview(file_path)

    def update_agent_status(self, text):
        if text:
            self.agent_status_label.setText(text)
            self.agent_status_label.show()
        else:
            self.agent_status_label.hide()

    def on_mic_changed(self, index):
        device_idx = self.mic_combo.itemData(index)
        if device_idx == -1:
            ui_comm.change_mic_signal.emit(-1) # -1 o None indicará default
        else:
            ui_comm.change_mic_signal.emit(device_idx)

    def on_text_entered(self):
        text = self.inbox.text()
        if text.strip():
            ui_comm.text_input_signal.emit(text)
            self.inbox.clear()
            self.inbox.clearFocus()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            self.is_dragging = True
            self.update_all_widgets_layout()
            event.accept()


    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.single_click_timer.stop() # Cancelar el single click para no activar a Miku
            
            if self.scale_factor == 0.5:
                self.scale_factor = 0.25 # Mini mode
                self.inbox.hide()
                self.mic_combo.hide()
                self.pair_btn.hide()
            else:
                self.scale_factor = 0.5 # Normal mode
                self.inbox.show()
                self.mic_combo.show()
                self.pair_btn.show()
                
            if hasattr(self, 'music_widget') and self.music_widget:
                self.music_widget.set_miku_scale(self.scale_factor)
            
            # Replay current GIF to apply scale
            if self.movie and self.movie.fileName():
                filename = os.path.basename(self.movie.fileName())
                self.play_gif(filename, loop=True)
            event.accept()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_paths = [u.toLocalFile() for u in urls]
            if file_paths:
                # El QuickLook se activará DESPUÉS del análisis silencioso
                first = file_paths[0]
                
                # Send silent analysis command to LLM
                files_str = ", ".join(file_paths)
                msg = f"[SILENT_DROP] {first}"
                ui_comm.text_input_signal.emit(msg)
        event.acceptProposedAction()

    def trigger_assistant_action(self):
        ui_comm.wake_signal.emit()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                self.single_click_timer.start(250) # Esperar 250ms a ver si hay doble clic
            self.drag_position = None
            self.is_dragging = False
            event.accept()

    def play_gif(self, filename, loop=True, next_gif=None, next_loop=True):
        if self.movie:
            self.movie.stop()
            self.movie.deleteLater()
            
        path = os.path.join(self.base_path, filename)
        if not os.path.exists(path):
            print(f"Error: No se encontró el GIF {path}")
            return
            
        old_center = self.geometry().center()

        self.movie = QMovie(path)
        reader = QImageReader(path)
        size = reader.size()
        if not size.isEmpty():
            scaled_size = QSize(int(size.width() * self.scale_factor), int(size.height() * self.scale_factor))
            self.movie.setScaledSize(scaled_size)
            
        self.label.setMovie(self.movie)
        
        if next_gif:
            movie_ref = self.movie
            def check_end():
                if movie_ref.currentFrameNumber() == movie_ref.frameCount() - 1:
                    movie_ref.stop()
                    self.play_gif(next_gif, loop=next_loop)
            self.movie.frameChanged.connect(check_end)
            
        self.movie.start()
        
        # Ajustar el tamaño y mover de vuelta al centro original
        self.adjustSize()
        new_geo = self.geometry()
        new_geo.moveCenter(old_center)
        self.setGeometry(new_geo)

    def change_state(self, state):
        if state == self.current_state:
            return
        self.current_state = state
        
        if self.scale_factor == 0.5:
            self.inbox.show()
            self.mic_combo.show()
            self.pair_btn.show()
        else:
            self.inbox.hide()
            self.mic_combo.hide()
            self.pair_btn.hide()
        if state == "idle":
            if self.current_state == "thinking":
                self.play_gif("thinking-part3.gif", loop=False, next_gif="idle.gif", next_loop=True)
            else:
                self.play_gif("idle.gif", loop=True)
        elif state == "sleeping":
            self.play_gif("sleeping-part1.gif", loop=False, next_gif="sleeping-part2.gif", next_loop=True)
        elif state == "thinking":
            self.play_gif("thinking-part1.gif", loop=False, next_gif="thinking-part2.gif", next_loop=True)
        elif state == "talking":
            if self.current_state == "thinking":
                self.play_gif("thinking-part3.gif", loop=False, next_gif="TALKING.gif", next_loop=True)
            else:
                self.play_gif("TALKING.gif", loop=True)
                
        self.current_state = state

    def update_all_widgets_layout(self):
        screen = QApplication.primaryScreen().availableGeometry()
        current_y = screen.bottom() - 20
        
        widgets = []
        if hasattr(self, 'clock_widget'): widgets.append(self.clock_widget)
        if hasattr(self, 'weather_widget'): widgets.append(self.weather_widget)
        if hasattr(self, 'info_widget'): widgets.append(self.info_widget)
        if hasattr(self, 'universal_card'): widgets.append(self.universal_card)
        
        widgets.sort(key=lambda w: getattr(w, 'last_shown_time', 0), reverse=True)
        
        for w in widgets:
            if w.isVisible() and not getattr(w, 'was_dragged_out', False):
                x = screen.left() + 20
                y = current_y - w.height()
                
                if w.pos() == QPoint(0, 0):
                    w.move(x, y)
                elif w.pos().y() != y or w.pos().x() != x:
                    if not hasattr(w, 'pos_animation'):
                        w.pos_animation = QPropertyAnimation(w, b"pos")
                        w.pos_animation.setDuration(400)
                        w.pos_animation.setEasingCurve(QEasingCurve.Type.OutExpo)
                    w.pos_animation.stop()
                    w.pos_animation.setStartValue(w.pos())
                    w.pos_animation.setEndValue(QPoint(x, y))
                    w.pos_animation.start()
                    
                current_y = y - 15
                
        if hasattr(self, 'music_widget') and getattr(self.music_widget, 'is_showing', False):
            if not getattr(self.music_widget, 'is_pinned', False):
                if getattr(self.music_widget, 'mode', 1) == 0:
                    target_y = screen.bottom() - 20 - self.music_widget.height()
                    target_x = screen.right() - self.music_widget.width() - 20
                    self.music_widget.animate_to_pos(target_x, target_y)
                else:
                    mx = self.x() + (self.width() - self.music_widget.width()) // 2
                    movie_h = 140
                    if hasattr(self, 'scale_factor'):
                        movie_h = int(560 * self.scale_factor)
                    center_y = self.y() + (self.height() // 2)
                    bottom_of_gif = center_y + (movie_h // 2)
                    
                    if hasattr(self, 'scale_factor') and self.scale_factor == 0.5:
                        my = bottom_of_gif + 60
                    else:
                        my = bottom_of_gif - 15
                    self.music_widget.move(mx, my)

miku_app = None

def run_ui(devices=None):
    if devices is None:
        devices = []
    global miku_app
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    app.setQuitOnLastWindowClosed(False)
    
    miku_app = MikuFace(devices)
    
    tray = QSystemTrayIcon()
    
    # Intentar usar el ícono de la ventana o fallback
    if not miku_app.windowIcon().isNull():
        tray.setIcon(miku_app.windowIcon())
    else:
        # Fallback a un icono del sistema si no hay icono custom
        tray.setIcon(app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon))
        
    tray.setToolTip("Miku Desktop")
    
    menu = QMenu()
    show_action = QAction("Mostrar Miku")
    show_action.triggered.connect(miku_app.show)
    hide_action = QAction("Ocultar Miku")
    hide_action.triggered.connect(miku_app.hide)
    
    settings_action = QAction("Configuraciones...")
    settings_action.triggered.connect(lambda: miku_app.show_settings())
    
    quit_action = QAction("Salir Completamente")
    quit_action.triggered.connect(app.quit)
    
    menu.addAction(show_action)
    menu.addAction(hide_action)
    menu.addAction(settings_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    
    tray.setContextMenu(menu)
    tray.setVisible(True)
    
    # Mover a la esquina inferior derecha por defecto (Modo Mascota)
    miku_app.show()
    screen = app.primaryScreen().availableGeometry()
    x = screen.width() - miku_app.width() - 50
    y = screen.height() - miku_app.height() - 50
    miku_app.move(x, y)
    
    sys.exit(app.exec())

def set_miku_state(state: str):
    ui_comm.change_state_signal.emit(state)
