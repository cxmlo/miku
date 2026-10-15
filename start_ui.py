import webview
import screeninfo
import webbrowser

class Api:
    def __init__(self, monitor_width=1920):
        self.window = None
        self.monitor_width = monitor_width
        self.settings_window = None

    def resize_window(self, width, height):
        if self.window:
            try:
                x_pos = int((self.monitor_width / 2) - (width / 2))
                self.window.resize(width, height)
                self.window.move(x_pos, 0)
            except Exception:
                try:
                    self.window.resize(width, height)
                except Exception:
                    pass

    def open_settings(self):
        try:
            webview.create_window(
                'Configuración · Miku',
                'http://127.0.0.1:8000/island/miku_settings.html',
                width=920,
                height=720,
                resizable=True
            )
        except Exception:
            webbrowser.open('http://127.0.0.1:8000/island/miku_settings.html')

def ensure_single_instance():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\MikuDynamicIslandSingleInstanceMutex"
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            print("[INFO] Miku ya está en ejecución. Enfocando ventana existente...")
            hwnd = ctypes.windll.user32.FindWindowW(None, "Miku Desktop")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            return False, None
        return True, mutex
    except Exception:
        return True, None

def main():
    ok, mutex = ensure_single_instance()
    if not ok:
        import sys
        sys.exit(0)

    try:
        monitor = screeninfo.get_monitors()[0]
        mon_w = monitor.width
    except Exception:
        mon_w = 1920

    api = Api(monitor_width=mon_w)
    initial_w = 360
    initial_h = 50
    x_pos = int((mon_w / 2) - (initial_w / 2))

    api.window = webview.create_window(
        'Miku Desktop',
        'http://127.0.0.1:8000/island/index.html',
        width=initial_w,
        height=initial_h,
        x=x_pos,
        y=0,
        frameless=True,
        transparent=True,
        on_top=True,
        resizable=False,
        js_api=api
    )
    
    webview.start()

if __name__ == '__main__':
    main()
