import winreg
import os
import sys

def register():
    ico_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "miku_ui", "src-tauri", "icons", "icon_link.ico"))
    
    # Robust command using parameter passing avoiding escaping issues with quotes in filenames
    cmd_str = (
        'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command '
        '"$path = $args[0]; if ($path) { try { Invoke-RestMethod -Uri \'http://127.0.0.1:8000/api/desktop/send_file_to_phone\' '
        '-Method Post -ContentType \'application/json\' -Body (@{path=$path} | ConvertTo-Json) -TimeoutSec 5 } '
        'catch { Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('
        '\'Miku Desktop no parece estar en ejecucion. Abre Miku para transferir archivos a tu celular.\', \'Miku-Link\') } }" \"%1\"'
    )
    
    targets = [
        r"Software\Classes\*\shell\MikuSendToPhone",
        r"Software\Classes\Directory\shell\MikuSendToPhone"
    ]
    
    for key_path in targets:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Enviar a Mi teléfono (Miku)")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, ico_path)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\command") as cmd_key:
            winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, cmd_str)

    # También registrar en el menú 'Enviar a...' (SendTo) de Windows
    sendto_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "SendTo")
    if os.path.exists(sendto_dir):
        sendto_cmd_path = os.path.join(sendto_dir, "Mi teléfono (Miku).cmd")
        try:
            with open(sendto_cmd_path, "w", encoding="utf-8") as f:
                f.write('@echo off\n')
                f.write('if "%~1"=="" exit /b\n')
                f.write(f'{cmd_str.replace("%1", "%~1")}\n')
            print(f"SUCCESS: SendTo shortcut created at {sendto_cmd_path}")
        except Exception as e:
            print(f"Warning: Could not create SendTo shortcut: {e}")

    print("SUCCESS: Context menu registered in Windows Registry for files and folders!")

if __name__ == "__main__":
    register()
