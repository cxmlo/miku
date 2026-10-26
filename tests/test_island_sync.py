from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI_SRC = ROOT / "miku_ui" / "src"

REQUIRED_FRONTEND_FILES = [
    "index.html",
    "island.css",
    "island.js",
    "miku_settings.html",
    "settings.css",
    "settings.js",
    "bridge.js",
    "sound_fx.js",
    "assets/app_icon.png",
    "assets/app_character.jpg",
]

def test_canonical_tauri_frontend_files_exist():
    """Verifica que todos los archivos modulares del frontend existan y no estén vacíos."""
    for rel_path in REQUIRED_FRONTEND_FILES:
        target = UI_SRC / rel_path
        assert target.exists(), f"Archivo requerido ausente: {rel_path}"
        assert target.stat().st_size > 0, f"Archivo vacío: {rel_path}"
