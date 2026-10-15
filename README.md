<div align="center">

<img src="assets/app_icon.png" width="108" alt="Miku Desktop icon" style="border-radius: 26px; box-shadow: 0 12px 32px rgba(0,0,0,0.35);">

# Miku Desktop

**A lively, smart desktop companion living in a Dynamic Island on your screen — orchestrating LLMs, controlling your PC, and keeping an eye on your coding agents.**

Watch your agents work, approve actions, listen to Spotify, drop files, and chat with your favorite AI models — all from a floating, non-intrusive island.

[![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-0078D4?logo=windows&logoColor=white)](https://github.com)
[![Tauri 2](https://img.shields.io/badge/Tauri-2-FFC131?logo=tauri&logoColor=black)](https://tauri.app)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v0.1.0--beta-orange)](https://github.com)

**[English](README.md)** · **[Español](README.es.md)**

</div>

> [!WARNING]
> **Public Beta Notice**: Miku Desktop is currently in **v0.1.0-beta**. You may encounter experimental features or occasional bugs. Feedback, bug reports, and pull requests are warmly welcome!

---

## Why

Desktop AI assistants are either bulky chat windows that steal your screen or corporate utilities without soul.
**Miku is the open, character-first companion.** Every line of code, animation, and integration is open-source — free to use, customize, read, fork, and remix.

Meet **Miku**: a soft, glossy cloud character that peeks out from the top of your screen, waves hello, follows your cursor with spherical eye tracking, reacts when you poke it, detects what song is playing on your PC, and notifies you the second your coding agents need your attention.

---

## Features

- **Dynamic Island on Windows** — sits quietly at the top edge of your screen. Hover over it to peek in; click to expand. Never steals window focus.
- **Multi-LLM Brain with Automatic Failover** — connect Google Gemini (Flash / Pro), Groq (Llama 3.3 70B & Whisper), Claude 3.5 Sonnet, or OpenAI GPT-4o. You can configure multiple backup keys per provider (`key1, key2`) and Miku rotates automatically on Rate Limits (Error 429).
- **Custom Agent Studio** — build your own specialized agents directly inside Settings: assign a custom persona prompt, tools, dedicated MCP servers, and custom API keys.
- **Live Coding Agent Hooks** — watch **Claude Code**, **Cursor**, **Codex**, or your custom scripts work in real time:
  - Thinking? Miku enters `thinking` mode.
  - Asking for command/file permissions? An approval card appears right inside the island.
  - Finished? Miku jumps with a happy emote.
- **Zero-Config Spotify & Media** — automatically detects and displays track titles and artists from Spotify, YouTube, or your browser without requiring Spotify Developer API tokens. Play, pause, or skip tracks with one click.
- **Drag & Drop Files** — drag any file or image directly into the Island. Miku analyzes it silently, provides an instant quicklook preview card, and answers questions about it.
- **Model Context Protocol (MCP)** — plug in SQLite databases, local filesystem explorers, Google Drive, or semantic vector memories dynamically.
- **Miku-Link Mobile Gateway** — pair your phone in seconds via QR code over your local Wi-Fi or free Cloudflare Quick Tunnels to sync clipboard, files, and mobile widgets.
- **Custom Personalities** — switch between **Calm** (mature and analytical), **Casual** (energetic gamer friend), and **Code** (concise senior engineer pair-programmer).

---

## Things to Try

| Action | What Miku Does |
| :--- | :--- |
| **Hover the top edge** | Peeks out and waves hello |
| **Move your mouse around** | Eyes follow your cursor with smooth 3D projection |
| **Click Miku** | Squishes, reacts, and shows emote feedback |
| **Play music on Spotify** | Displays live album art, track title, and media controls |
| **Drag a file onto the Island** | Swallows the file and displays an instant analysis card |
| **Run Claude Code in terminal** | Notifies you on tool use and permission requests |

---

## Install

### Windows Executable (.exe — Recommended)

1. Grab the latest `Miku Desktop_0.1.0_x64-setup.exe` from [Releases](https://github.com/cxmlo/miku/releases).
2. Run the installer and launch **Miku Desktop**.
3. Open **Settings** from the island to paste your preferred API key (e.g., free Gemini Flash from Google AI Studio).

### Build from Source

**Requirements**:
- Windows 10/11 x64
- [Python 3.12+](https://python.org)
- [Node.js 18+](https://nodejs.org)
- [Rust & Cargo](https://rustup.rs)

```powershell
# 1. Clone the repository
git clone https://github.com/cxmlo/miku.git
cd miku

# 2. Setup Python backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. Setup environment variables
cp .env.example .env
# Edit .env with your API keys

# 4. Run the desktop app in development mode
cd miku_ui
npm install
npm run tauri dev
```

---

## Creating & Integrating Custom Agents

### Option 1: Visual No-Code Creator (Inside the App)
1. Open the Island and click **Ajustes (Settings) → Agentes**.
2. Click **Crear agente**:
   - Give it a name (e.g. *DevOps Bot*, *Writer*, *Game Companion*).
   - Type your custom **System Prompt / Instructions**.
   - Assign an **MCP server** (Filesystem, SQLite, Google Drive, etc.).
   - (Optional) Assign a dedicated API key.
3. Your agent appears instantly in the dock and Island selector!

### Option 2: CLI & Terminal Hooks (Claude Code, Cursor, Python scripts)
You can connect any terminal tool or custom script to Miku using the built-in CLI helper:

```bash
# Notify Miku that your agent is working on a task:
python scripts/miku_hook.py "Refactoring auth module..." --agent "MyAgent" --event PreToolUse

# Request user permission from the Island:
python scripts/miku_hook.py "Allow deleting old build folder?" --event PermissionRequest

# Notify completion:
python scripts/miku_hook.py "Deployment finished!" --event Stop
```

In **Claude Code**, simply add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "UserPromptSubmit": "python \"C:\\path\\to\\miku\\scripts\\miku_hook.py\" \"$PROMPT\" -e UserPromptSubmit -a claude",
    "PreToolUse": "python \"C:\\path\\to\\miku\\scripts\\miku_hook.py\" \"$TOOL\" -e PreToolUse -a claude",
    "Stop": "python \"C:\\path\\to\\miku\\scripts\\miku_hook.py\" \"Done\" -e Stop -a claude"
  }
}
```

---

## How It Works

- **Island Frontend**: Built with [Tauri 2](https://tauri.app) (Rust + Webview). The character is rendered at 60 fps on an HTML5 2D Canvas with spring dynamics, smooth gaze tracking, and zero heavyweight 3D engines.
- **Python Gateway (`server.py`)**: A high-performance FastAPI and WebSocket service handling speech recognition, local wake-word detection, MCP tools, and LLM streaming.
- **Multi-LLM Failover (`brain.py`)**: Routes semantic requests based on task complexity (reasoning, vision, code) and manages automatic key pooling.
- **Privacy First**: API keys remain securely on your local machine in `.env` and `settings_config.json`. Miku connects only to the endpoints you choose.

---

## Contributing

Contributions, bug reports, and feature ideas are warmly welcome!
If you find a bug or have a suggestion, please open an Issue or submit a Pull Request.

---

## Credits

- Created and maintained by **[cxmlo](https://github.com/cxmlo)**.

---

## License

This project is open-source under the **[MIT License](LICENSE)**. You are free to use, modify, learn from, and distribute this software, as long as the original copyright notice is preserved.
