import json
import os

CONTACTS_FILE = "miku_contacts.json"

def _load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return {}
    try:
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_contacts(data):
    try:
        with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error al guardar contactos: {e}")

def asociar_contacto_app(contacto: str, app: str, nombre_en_interfaz: str = None) -> str:
    """Asocia un contacto con una aplicación en la memoria a largo plazo. También permite guardar cómo aparece en la interfaz."""
    # Normalizar para evitar duplicados por mayúsculas
    contacto_key = contacto.strip().lower()
    app = app.strip()
    
    contacts = _load_contacts()
    
    if contacto_key not in contacts:
        contacts[contacto_key] = {
            "nombre_original": contacto,
            "apps": []
        }
        
    apps = [a.lower() for a in contacts[contacto_key]["apps"]]
    
    # Manejo del alias
    mensaje_extra = ""
    if nombre_en_interfaz:
        contacts[contacto_key]["nombre_en_interfaz"] = nombre_en_interfaz.strip()
        mensaje_extra = f" Además, recordaré que en la app aparece como '{nombre_en_interfaz}'."
        
    if app.lower() not in apps:
        contacts[contacto_key]["apps"].append(app)
        _save_contacts(contacts)
        return f"Éxito: Ahora recordaré que '{contacto}' usa la aplicación '{app}'.{mensaje_extra}"
    else:
        if nombre_en_interfaz:
            _save_contacts(contacts)
            return f"El contacto '{contacto}' ya estaba asociado a '{app}'. Se actualizó su nombre en interfaz a '{nombre_en_interfaz}'."
        return f"El contacto '{contacto}' ya estaba asociado a '{app}'."

def obtener_contactos_str() -> str:
    """Devuelve un string formateado con todos los contactos y sus apps para inyectarlo en el prompt."""
    contacts = _load_contacts()
    if not contacts:
        return "Libreta de contactos vacía."
        
    resultado = "LIBRETA DE CONTACTOS CONOCIDOS:\n"
    for key, data in contacts.items():
        nombre = data.get("nombre_original", key)
        apps = ", ".join(data.get("apps", []))
        
        alias = data.get("nombre_en_interfaz", "")
        if alias:
            resultado += f"- {nombre} (En la app aparece como: '{alias}'): {apps}\n"
        else:
            resultado += f"- {nombre}: {apps}\n"
    return resultado
