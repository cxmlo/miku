import sys
import os
import shutil
import urllib.request
import urllib.parse
import json
import tkinter as tk
from threading import Thread
import time

def send_files(ui_update_cb, ui_close_cb):
    import tempfile
    downloads_path = tempfile.gettempdir()
    os.makedirs(downloads_path, exist_ok=True)
    
    files_to_send = [f for f in sys.argv[1:] if os.path.isfile(f)]
    if not files_to_send:
        ui_update_cb("> No hay archivos válidos.")
        time.sleep(2)
        ui_close_cb()
        return

    for file_path in files_to_send:
        filename = os.path.basename(file_path)
        dest_path = os.path.join(downloads_path, filename)
        
        ui_update_cb(f"> Preparando: {filename[:20]}...")
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copy2(file_path, dest_path)
        
        time.sleep(0.5)
        ui_update_cb("> Conectando con Miku...")
        
        url = "http://127.0.0.1:8000/api/desktop/trigger_phone_download"
        data = json.dumps({"filename": filename}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            urllib.request.urlopen(req, timeout=3)
            ui_update_cb("> Enviado exitosamente.")
        except Exception as e:
            ui_update_cb("> Miku no está en línea.")
        
        time.sleep(1.5)
        
    ui_close_cb()

def main():
    if len(sys.argv) < 2:
        sys.exit(0)
        
    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg="#000000")
    
    # Center the window
    w = 320
    h = 80
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    
    # Border
    frame = tk.Frame(root, bg="#ffffff", bd=1)
    frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    inner_frame = tk.Frame(frame, bg="#000000")
    inner_frame.pack(fill=tk.BOTH, expand=True)

    lbl_title = tk.Label(inner_frame, text="MIKU LINK", fg="#ffffff", bg="#000000", font=("Consolas", 12, "bold"))
    lbl_title.pack(pady=(10, 0))
    
    lbl_status = tk.Label(inner_frame, text="> Iniciando...", fg="#cccccc", bg="#000000", font=("Consolas", 9))
    lbl_status.pack(pady=(5, 10))

    def update_status(text):
        lbl_status.config(text=text)
        root.update()
        
    def close_ui():
        root.destroy()
        
    # Run the send task in a thread so UI doesn't freeze
    t = Thread(target=send_files, args=(update_status, close_ui), daemon=True)
    t.start()
    
    root.mainloop()

if __name__ == "__main__":
    main()
