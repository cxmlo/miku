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

def main():
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
