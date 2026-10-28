import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QPushButton, QListWidget, QLineEdit, QFileDialog, 
    QMessageBox, QInputDialog, QFormLayout, QSpinBox, QCheckBox,
    QGroupBox, QScrollArea, QComboBox
)
from PyQt6.QtCore import Qt

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_config.json")
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
MODELS_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_config.json")

# ─── Definición de claves de API ──────────────────────────────────────────────

API_KEYS_CONFIG = [
    {
        "group": "Modelos de IA (LLM)",
        "keys": [
            {"env": "GROQ_API_KEY", "label": "Groq API Key", "hint": "Para transcripción rápida (Whisper). Obtener en: console.groq.com"},
            {"env": "GEMINI_API_KEY", "label": "Google AI Studio API Key", "hint": "¡Requerida para modelos Gemini 3.x Flash! Obtener en: aistudio.google.com/app/apikey"},
            {"env": "GOOGLE_CLOUD_PROJECT", "label": "Google Cloud Project ID", "hint": "ID del proyecto (ej. mi-proyecto-12345) (Solo Vertex AI 2.5 Pro)"},
            {"env": "GOOGLE_CLOUD_LOCATION", "label": "Google Cloud Location", "hint": "Región del proyecto (ej. us-central1, global)"},
            {"env": "NVIDIA_API_KEY", "label": "NVIDIA API Key", "hint": "Para modelos NVIDIA NIM. Obtener en: build.nvidia.com"},
            {"env": "OPENAI_API_KEY", "label": "OpenAI API Key", "hint": "Para GPT-4o. Obtener en: platform.openai.com"},
            {"env": "ANTHROPIC_API_KEY", "label": "Claude (Anthropic) API Key", "hint": "Para Claude Opus/Sonnet. Obtener en: console.anthropic.com"},
        ]
    },
    {
        "group": "Spotify",
        "keys": [
            {"env": "SPOTIFY_CLIENT_ID", "label": "Spotify Client ID", "hint": "Dashboard: developer.spotify.com/dashboard"},
            {"env": "SPOTIFY_CLIENT_SECRET", "label": "Spotify Client Secret", "hint": "Se obtiene del mismo dashboard de Spotify"},
            {"env": "SPOTIFY_REDIRECT_URI", "label": "Spotify Redirect URI", "hint": "Usa: http://localhost:8080"},
        ]
    },
    {
        "group": "Seguridad",
        "keys": [
            {"env": "MIKU_API_KEY", "label": "Miku API Key", "hint": "Clave para autenticar WebSocket (por defecto: miku_secure_key_2026)"},
        ]
    },
]

# ─── Modelos Disponibles por Rol ──────────────────────────────────────────────

AVAILABLE_MODELS = {
    "chat": [
        {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (Vertex AI)", "provider": "google"},
        {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash (Vertex AI)", "provider": "google"},
        {"id": "gemini-3.6-flash", "name": "Gemini 3.6 Flash (Vertex AI)", "provider": "google"},
        {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (Vertex AI)", "provider": "google"},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro (Google AI Studio)", "provider": "google"},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (Google AI Studio)", "provider": "google"},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (Anthropic)", "provider": "anthropic"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus (Anthropic)", "provider": "anthropic"},
        {"id": "gpt-4o", "name": "GPT-4o (OpenAI)", "provider": "openai"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (OpenAI)", "provider": "openai"},
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Groq)", "provider": "groq"},
    ],
    "computer_use": [
        {"id": "gemini-2.5-computer-use-preview-10-2025", "name": "Gemini 2.5 Computer Use Preview (Vertex AI)", "provider": "google"},
        {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (Google AI Studio - Requiere API Key)", "provider": "google"},
        {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash (Google AI Studio - Requiere API Key)", "provider": "google"},
        {"id": "gemini-3.6-flash", "name": "Gemini 3.6 Flash (Google AI Studio - Requiere API Key)", "provider": "google"},
        {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (Google AI Studio - Requiere API Key)", "provider": "google"},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (Recomendado - Antropic)", "provider": "anthropic"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Vertex AI)", "provider": "google"},
        {"id": "gpt-4o", "name": "GPT-4o (OpenAI)", "provider": "openai"},
    ],
    "stt": [
        {"id": "whisper-large-v3", "name": "Whisper Large v3 (Groq - Muy rápido)", "provider": "groq"},
        {"id": "whisper-large-v3-turbo", "name": "Whisper Large v3 Turbo (Groq)", "provider": "groq"},
        {"id": "whisper-1", "name": "Whisper v1 (OpenAI)", "provider": "openai"},
    ]
}


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuraciones de Miku")
        self.setMinimumSize(650, 550)
        
        self.mcp_config = self.load_config(CONFIG_PATH, {"servidores": {}})
        self.models_config = self.load_config(MODELS_CONFIG_PATH, {
            "chat": "gemini-1.5-flash",
            "computer_use": "gemini-1.5-flash",
            "stt": "whisper-large-v3"
        })
        self.env_vars = self._load_env()
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Pestañas
        self.tabs.addTab(self.create_api_keys_tab(), "🔑 Claves de IA")
        self.tabs.addTab(self.create_models_tab(), "🧠 Modelos (Router)")
        self.tabs.addTab(self.create_alerts_tab(), "🔔 Alertas Proactivas")
        self.tabs.addTab(self.create_mcp_tab(), "🔌 Servidores MCP")
        self.tabs.addTab(self.create_permissions_tab(), "📁 Permisos FS")
        
        # Botones de Acción
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Guardar Cambios")
        save_btn.clicked.connect(self.save_and_close)
        save_btn.setStyleSheet("padding: 8px 20px; font-weight: bold;")
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("padding: 8px 20px;")
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    # ─── Config handling ──────────────────────────────────────────────────────
    
    def load_config(self, path, default):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error cargando {path}: {e}")
        return default

    def _load_env(self) -> dict:
        """Carga las variables del archivo .env como diccionario."""
        env_vars = {}
        try:
            if os.path.exists(ENV_PATH):
                with open(ENV_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, _, value = line.partition("=")
                            env_vars[key.strip()] = value.strip().strip("'\"")
        except Exception:
            pass
        return env_vars
    
    def _save_env(self):
        """Guarda las variables de vuelta al archivo .env."""
        try:
            lines = ["# Claves de API para Miku V2\n"]
            lines.append("# Generado automáticamente por Miku Settings\n\n")
            
            for group in API_KEYS_CONFIG:
                lines.append(f"# {group['group']}\n")
                for key_info in group["keys"]:
                    env_key = key_info["env"]
                    value = self.env_vars.get(env_key, "")
                    if value:
                        lines.append(f"{env_key}={value}\n")
                    else:
                        lines.append(f"# {env_key}=\n")
                lines.append("\n")
            
            # Preservar claves extra que no están en nuestra definición
            known_keys = set()
            for group in API_KEYS_CONFIG:
                for key_info in group["keys"]:
                    known_keys.add(key_info["env"])
            
            extras = {k: v for k, v in self.env_vars.items() if k not in known_keys}
            if extras:
                lines.append("# Otras configuraciones\n")
                for k, v in extras.items():
                    lines.append(f"{k}={v}\n")
            
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar .env:\n{e}")
            return False

    # ─── API Keys Tab ─────────────────────────────────────────────────────────

    def create_api_keys_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        
        info_label = QLabel(
            "Configura aquí tus claves de API. Miku necesita al menos una clave de LLM "
            "(Groq es obligatoria para la voz) y opcionalmente las demás para funciones extra."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #aaa; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        self.api_key_inputs: dict[str, QLineEdit] = {}
        
        for group in API_KEYS_CONFIG:
            group_box = QGroupBox(group["group"])
            group_layout = QFormLayout()
            group_box.setLayout(group_layout)
            
            for key_info in group["keys"]:
                env_key = key_info["env"]
                
                input_field = QLineEdit()
                input_field.setPlaceholderText(key_info["hint"])
                input_field.setText(self.env_vars.get(env_key, ""))
                
                # Ocultar claves sensibles por defecto
                if "key" in env_key.lower() or "secret" in env_key.lower():
                    input_field.setEchoMode(QLineEdit.EchoMode.Password)
                
                # Botón para mostrar/ocultar
                row_layout = QHBoxLayout()
                row_layout.addWidget(input_field)
                
                if "key" in env_key.lower() or "secret" in env_key.lower():
                    toggle_btn = QPushButton("👁")
                    toggle_btn.setFixedWidth(30)
                    toggle_btn.setCheckable(True)
                    toggle_btn.toggled.connect(
                        lambda checked, field=input_field: field.setEchoMode(
                            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
                        )
                    )
                    row_layout.addWidget(toggle_btn)
                
                row_widget = QWidget()
                row_widget.setLayout(row_layout)
                group_layout.addRow(key_info["label"] + ":", row_widget)
                
                self.api_key_inputs[env_key] = input_field
            
            layout.addWidget(group_box)
        
        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    # ─── Models Tab ───────────────────────────────────────────────────────────

    def _is_provider_configured(self, provider: str) -> bool:
        """Verifica si el usuario ingresó la API key para un proveedor."""
        # Leemos directo de self.env_vars, asumiendo que es la configuración actual.
        if provider == "google":
            return bool(self.env_vars.get("GOOGLE_CLOUD_PROJECT", "").strip())
        elif provider == "anthropic":
            return bool(self.env_vars.get("ANTHROPIC_API_KEY", "").strip())
        elif provider == "openai":
            return bool(self.env_vars.get("OPENAI_API_KEY", "").strip())
        elif provider == "groq":
            return bool(self.env_vars.get("GROQ_API_KEY", "").strip())
        return True

    def create_models_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel(
            "Selecciona qué Inteligencia Artificial realizará cada tipo de tarea.\n"
            "Solo se muestran los modelos de los proveedores para los que has configurado "
            "una clave de API en la primera pestaña (requiere guardar cambios y reabrir esta ventana para actualizar la lista)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #aaa; margin-bottom: 15px;")
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        self.model_combos = {}
        
        roles = [
            ("chat", "💭 Inteligencia Principal (Chat General)", "El cerebro principal de Miku para conversación."),
            ("computer_use", "💻 Control de PC (Computer Use)", "El agente que controla el mouse y programas."),
            ("stt", "🎙️ Transcripción de Voz (STT)", "El modelo que transcribe tu voz a texto.")
        ]
        
        for role_key, label_text, tooltip in roles:
            combo = QComboBox()
            combo.setToolTip(tooltip)
            
            current_val = self.models_config.get(role_key, "")
            index_to_select = 0
            added_count = 0
            
            # Filtrar modelos según proveedores configurados
            for model in AVAILABLE_MODELS[role_key]:
                if self._is_provider_configured(model["provider"]):
                    combo.addItem(model["name"], userData=model)
                    if model["id"] == current_val:
                        index_to_select = added_count
                    added_count += 1
            
            if added_count == 0:
                combo.addItem("No hay APIs configuradas para este rol", userData={"id": ""})
                combo.setEnabled(False)
            else:
                combo.setCurrentIndex(index_to_select)
                
            self.model_combos[role_key] = combo
            form_layout.addRow(label_text + ":", combo)
            
        layout.addLayout(form_layout)
        layout.addStretch()
        return widget

    # ─── Alerts Config Tab ────────────────────────────────────────────────────

    def create_alerts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel(
            "Configura cuándo Miku te avisa sobre tu uso del PC.\n"
            "Los umbrales indican cuántas horas de uso continuo disparan una alerta."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #aaa; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        self.alert_config = {}
        
        alerts_data = [
            ("juego", "🎮 Juegos (Valorant, LoL, Minecraft...)", 120),
            ("ocio", "💬 Ocio / Redes Sociales (Discord, Telegram...)", 180),
            ("trabajo", "💻 Trabajo sin descanso (VSCode, IDEs...)", 120),
            ("navegador", "🌐 Navegación excesiva (Chrome, Opera...)", 180),
        ]
        
        for key, label, default_min in alerts_data:
            group = QGroupBox(label)
            gl = QHBoxLayout()
            
            enabled_cb = QCheckBox("Activar alerta")
            enabled_cb.setChecked(True)
            gl.addWidget(enabled_cb)
            
            gl.addWidget(QLabel("Umbral:"))
            spinbox = QSpinBox()
            spinbox.setRange(30, 600)
            spinbox.setValue(default_min)
            spinbox.setSuffix(" min")
            gl.addWidget(spinbox)
            
            gl.addStretch()
            group.setLayout(gl)
            layout.addWidget(group)
            
            self.alert_config[key] = {"enabled": enabled_cb, "threshold": spinbox}
        
        layout.addStretch()
        return widget

    # ─── MCP Tab ──────────────────────────────────────────────────────────────

    def save_mcp_config(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.mcp_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar config MCP:\n{e}")
            return False

    def create_mcp_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Servidores MCP Registrados:"))
        
        self.mcp_list = QListWidget()
        self.refresh_mcp_list()
        layout.addWidget(self.mcp_list)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Añadir Servidor")
        add_btn.clicked.connect(self.add_mcp)
        del_btn = QPushButton("Eliminar Seleccionado")
        del_btn.clicked.connect(self.del_mcp)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)
        
        return widget

    def refresh_mcp_list(self):
        self.mcp_list.clear()
        servidores = self.mcp_config.get("servidores", {})
        for name, data in servidores.items():
            cmd = data.get("command", "")
            args = " ".join(data.get("args", []))
            self.mcp_list.addItem(f"{name} ({cmd} {args})")

    def add_mcp(self):
        name, ok1 = QInputDialog.getText(self, "Nuevo MCP", "Nombre del servidor (ej. sqlite):")
        if ok1 and name:
            cmd, ok2 = QInputDialog.getText(self, "Comando MCP", "Comando base (ej. npx, uvx):")
            if ok2 and cmd:
                args_str, ok3 = QInputDialog.getText(self, "Argumentos MCP", "Argumentos separados por espacio:")
                if ok3:
                    if "servidores" not in self.mcp_config:
                        self.mcp_config["servidores"] = {}
                    import shlex
                    self.mcp_config["servidores"][name] = {
                        "command": cmd,
                        "args": shlex.split(args_str)
                    }
                    self.refresh_mcp_list()

    def del_mcp(self):
        selected = self.mcp_list.currentRow()
        if selected >= 0:
            item_text = self.mcp_list.item(selected).text()
            name = item_text.split(" ")[0]
            if name in self.mcp_config.get("servidores", {}):
                del self.mcp_config["servidores"][name]
                self.refresh_mcp_list()

    # ─── Permissions Tab ──────────────────────────────────────────────────────

    def create_permissions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Directorios Permitidos para Miku (File System MCP):"))
        
        self.dir_list = QListWidget()
        self.refresh_dir_list()
        layout.addWidget(self.dir_list)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Añadir Carpeta")
        add_btn.clicked.connect(self.add_dir)
        del_btn = QPushButton("Quitar Seleccionada")
        del_btn.clicked.connect(self.del_dir)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)
        
        return widget
        
    def refresh_dir_list(self):
        self.dir_list.clear()
        fs_config = self.mcp_config.get("servidores", {}).get("file_system", {})
        args = fs_config.get("args", [])
        paths = args[2:] if len(args) > 2 else []
        for path in paths:
            self.dir_list.addItem(path)

    def add_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if folder:
            fs_config = self.mcp_config.get("servidores", {}).get("file_system", {})
            args = fs_config.get("args", [])
            if len(args) < 2:
                args = ["-y", "@modelcontextprotocol/server-filesystem"]
                
            folder_normalized = folder.replace("/", "\\")
            if folder_normalized not in args:
                args.append(folder_normalized)
                fs_config["args"] = args
                if "servidores" not in self.mcp_config:
                    self.mcp_config["servidores"] = {}
                self.mcp_config["servidores"]["file_system"] = fs_config
                self.refresh_dir_list()

    def del_dir(self):
        selected = self.dir_list.currentRow()
        if selected >= 0:
            path_to_remove = self.dir_list.item(selected).text()
            fs_config = self.mcp_config.get("servidores", {}).get("file_system", {})
            args = fs_config.get("args", [])
            if path_to_remove in args:
                args.remove(path_to_remove)
                self.refresh_dir_list()

    # ─── Save All ─────────────────────────────────────────────────────────────

    def save_and_close(self):
        # 1. Guardar API keys al .env
        for env_key, input_field in self.api_key_inputs.items():
            value = input_field.text().strip()
            if value:
                self.env_vars[env_key] = value
            elif env_key in self.env_vars:
                del self.env_vars[env_key]
        env_saved = self._save_env()
        
        # 2. Guardar config MCP
        mcp_saved = self.save_mcp_config()
        
        # 3. Guardar config de Modelos
        try:
            for role_key, combo in self.model_combos.items():
                model_data = combo.currentData()
                self.models_config[role_key] = model_data["id"]
                # También podríamos guardar el provider en otro config si queremos, 
                # pero el id suele ser único y suficiente.
            with open(MODELS_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.models_config, f, indent=2)
        except Exception as e:
            print(f"Error guardando modelos: {e}")
        
        # 4. Guardar config de Alertas
        try:
            alerts_config = {}
            for key, widgets in self.alert_config.items():
                alerts_config[key] = {
                    "enabled": widgets["enabled"].isChecked(),
                    "threshold_minutes": widgets["threshold"].value()
                }
            alerts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "alerts_config.json")
            os.makedirs(os.path.dirname(alerts_path), exist_ok=True)
            with open(alerts_path, "w", encoding="utf-8") as f:
                json.dump(alerts_config, f, indent=2)
        except Exception as e:
            print(f"Error guardando alertas: {e}")
        
        if env_saved and mcp_saved:
            QMessageBox.information(
                self, "Guardado", 
                "Configuración guardada exitosamente.\n\n"
                "Debes reiniciar Miku Desktop (cerrar y volver a abrir) "
                "para que los cambios en API Keys, Modelos y MCP surtan efecto."
            )
            self.accept()



if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    dialog.show()
    sys.exit(app.exec())

