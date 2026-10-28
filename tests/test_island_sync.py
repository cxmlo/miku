from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
UI_SRC = ROOT / "miku_ui" / "src"

REQUIRED_FRONTEND_FILES = [
    "index.html",
    "island.css",
    "island.js",
    "miku_settings.html",
    "settings.css",
    "settings.js",
    "miku_ui.css",
    "miku_ui.js",
    "bridge.js",
    "sound_fx.js",
    "styles/tokens.css",
    "styles/base.css",
    "styles/components.css",
    "styles/miku-link.css",
    "i18n/es.js",
    "components/index.js",
    "components/primitives.js",
    "components/feedback.js",
    "components/overlays.js",
    "components/interactive.js",
    "components/particlesHeader.js",
    "components/qrPhone.js",
    "sections/mikuLinkSection.js",
    "services/mikuLinkService.js",
    "assets/app_icon.png",
    "assets/app_character.jpg",
]

def test_canonical_tauri_frontend_files_exist():
    """Verifica que todos los archivos modulares del frontend existan y no estén vacíos."""
    for rel_path in REQUIRED_FRONTEND_FILES:
        target = UI_SRC / rel_path
        assert target.exists(), f"Archivo requerido ausente: {rel_path}"
        assert target.stat().st_size > 0, f"Archivo vacío: {rel_path}"

def test_design_system_css_no_hardcoded_hex_outside_tokens():
    """Verifica que settings.css, miku_ui.css, styles/base.css, styles/components.css y styles/miku-link.css no contengan colores hexadecimales sueltos fuera de tokens.css."""
    css_files = [
        "settings.css",
        "miku_ui.css",
        "styles/base.css",
        "styles/components.css",
        "styles/miku-link.css",
    ]
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    for rel_path in css_files:
        content = (UI_SRC / rel_path).read_text(encoding="utf-8")
        # Permitir únicamente initial-value: #f5f5f7 dentro de @property --ac
        cleaned = re.sub(r"initial-value:\s*#[0-9a-fA-F]{3,8}", "", content)
        matches = hex_pattern.findall(cleaned)
        assert not matches, f"Colores hexadecimales hardcodeados en {rel_path}: {matches}"

