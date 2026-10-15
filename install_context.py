import winreg
import sys
import os

def add_context_menu():
    pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
    # Usar HKEY_CURRENT_USER para no requerir permisos de Administrador
    key_path = r"Software\Classes\*\shell\MikuLink"
    try:
        # Create key
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValue(key, "", winreg.REG_SZ, "🌸 Enviar al celular (Miku)")
        
        # Try to use python icon
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, pythonw_path)
        
        # Create command subkey
        cmd_key = winreg.CreateKey(key, "command")
        script_path = os.path.abspath("send_to_miku.py")
        cmd = f'"{pythonw_path}" "{script_path}" "%1"'
        winreg.SetValue(cmd_key, "", winreg.REG_SZ, cmd)
        print("Menú contextual registrado correctamente!")
    except Exception as e:
        print(f"Error: {e}")
        
    # También agregar a SendTo (Enviar a)
    try:
        import win32com.client
        sendto_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Roaming', 'Microsoft', 'Windows', 'SendTo')
        path = os.path.join(sendto_dir, 'Miku-Link.lnk')
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = pythonw_path
        shortcut.Arguments = f'"{os.path.abspath("send_to_miku.py")}"'
        shortcut.IconLocation = pythonw_path
        shortcut.save()
        print("Acceso directo SendTo creado!")
    except Exception as e:
        print(f"Error SendTo: {e}")

if __name__ == '__main__':
    add_context_menu()
