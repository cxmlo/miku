"""
scripts/build_sidecar.py - Compilador automatizado del backend de Miku para Tauri
Genera el binario independiente (sidecar) miku-core-x86_64-pc-windows-msvc.exe
utilizando PyInstaller para que la app instalada no dependa de tener Python instalado.
"""

import os
import stat
import sys
import shutil
import subprocess
import tempfile

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINARIES_DIR = os.path.join(WORKSPACE_DIR, "miku_ui", "src-tauri", "binaries")
TARGET_NAME = "miku-core-x86_64-pc-windows-msvc.exe"
LOCAL_APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Miku Desktop")

def _remove_readonly(func, path, _exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def run():
    print("=" * 60)
    print("[Miku Build] Construyendo Miku Core Sidecar para Tauri 2...")
    print("=" * 60)

    os.makedirs(BINARIES_DIR, exist_ok=True)
    build_dir = os.path.join(WORKSPACE_DIR, "build")
    os.makedirs(build_dir, exist_ok=True)
    work_dir = tempfile.mkdtemp(prefix="pyinstaller-miku-core-", dir=build_dir)

    # Buscar el ejecutable de PyInstaller
    venv_pyinstaller = os.path.join(WORKSPACE_DIR, "venv", "Scripts", "pyinstaller.exe")
    if os.path.exists(venv_pyinstaller):
        pyinstaller_bin = venv_pyinstaller
    else:
        pyinstaller_bin = "pyinstaller"

    # Modo por defecto: --onedir para arranque instantáneo (1s) sin tiempo de descompresión
    is_onefile = "--onefile" in sys.argv
    is_onedir = not is_onefile
    build_mode = "--onefile" if is_onefile else "--onedir"
    print(f"[Miku Build] Modo de empaquetado: {build_mode} {'(Binario único onefile)' if is_onefile else '(Carpeta onedir: arranque instantáneo en ~1s)'}")

    # Limpiar binarios y directorios previos si existen
    for target in [
        os.path.join(BINARIES_DIR, "miku-core"),
        os.path.join(BINARIES_DIR, "miku-core.exe"),
        os.path.join(BINARIES_DIR, TARGET_NAME)
    ]:
        if os.path.exists(target):
            try:
                if os.path.isdir(target):
                    shutil.rmtree(target, onerror=_remove_readonly)
                else:
                    os.remove(target)
            except Exception as e:
                print(f"[AVISO] No se pudo limpiar {target}: {e}")

    cmd = [
        pyinstaller_bin,
        "--name=miku-core",
        build_mode,
        "--noconfirm",
        "--console",
        "--clean",
        "--distpath=" + BINARIES_DIR,
        "--workpath=" + work_dir,
        "--specpath=" + build_dir,

        # Archivos de datos y configuraciones iniciales
        f"--add-data={os.path.join(WORKSPACE_DIR, 'Miku_20260622_080146.onnx')};.",
        f"--add-data={os.path.join(WORKSPACE_DIR, 'Miku_20260622_080146.tflite')};.",
        f"--add-data={os.path.join(WORKSPACE_DIR, 'wake.wav')};.",
        f"--add-data={os.path.join(WORKSPACE_DIR, 'agents_config.json')};.",
        f"--add-data={os.path.join(WORKSPACE_DIR, 'models_config.json')};.",
        f"--add-data={os.path.join(WORKSPACE_DIR, 'settings_config.json')};.",
        f"--paths={WORKSPACE_DIR}",
        # Módulos del proyecto
        "--hidden-import=computer_use",
        "--hidden-import=prompt_manager",
        "--hidden-import=contacts_memory",
        "--hidden-import=activity_monitor",
        "--hidden-import=agents",
        "--hidden-import=audio_handler",
        "--hidden-import=brain",
        "--hidden-import=config",
        "--hidden-import=mcp_client",
        "--hidden-import=memory",
        "--hidden-import=memory_temporal",
        "--hidden-import=miku_db",
        "--hidden-import=miku_paths",
        "--hidden-import=models_provider",
        "--hidden-import=music_controller",
        "--hidden-import=proactive_agent",
        "--hidden-import=security_manager",
        "--hidden-import=spatial_memory",
        "--hidden-import=tools",
        "--hidden-import=tools_code",
        "--hidden-import=tools_hardware",
        "--hidden-import=tools_media",
        "--hidden-import=tools_miku",
        "--hidden-import=tools_os",
        "--hidden-import=tools_spotify",
        "--hidden-import=tools_web",
        "--hidden-import=web_browser",
        # Hidden imports y paquetes dinámicos
        "--collect-all=chromadb",
        "--copy-metadata=chromadb",
        "--collect-all=litellm",
        "--collect-all=openwakeword",
        "--collect-all=onnxruntime",
        "--collect-all=winsdk",
        "--hidden-import=winsdk",
        "--hidden-import=chromadb.telemetry.product.posthog",
        "--hidden-import=chromadb.api.segment",
        "--hidden-import=chromadb.db.impl.sqlite",
        "--hidden-import=chromadb.segment.impl.vector.local_hnsw",
        "--hidden-import=chromadb.segment.impl.metadata.sqlite",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=engineio.async_drivers.asgi",
        "--hidden-import=sqlite3",
        "--hidden-import=sounddevice",
        "--hidden-import=pygame",
        "--hidden-import=fastapi",
        "--hidden-import=pydantic",
        "--collect-all=qrcode",
        "--hidden-import=qrcode",
        os.path.join(WORKSPACE_DIR, "server.py")
    ]

    # Incluir cloudflared.exe si existe en el workspace
    cf = os.path.join(WORKSPACE_DIR, "cloudflared.exe")
    if os.path.exists(cf):
        cmd.insert(cmd.index(os.path.join(WORKSPACE_DIR, "server.py")), f"--add-data={cf};.")

    print(f"[1/3] Ejecutando PyInstaller...")
    try:
        ret = subprocess.run(cmd, cwd=WORKSPACE_DIR)
    finally:
        shutil.rmtree(work_dir, onerror=_remove_readonly)
    if ret.returncode != 0:
        print("[ERROR] Error al compilar con PyInstaller.")
        sys.exit(ret.returncode)

    if is_onefile:
        raw_exe = os.path.join(BINARIES_DIR, "miku-core.exe")
        triple_exe = os.path.join(BINARIES_DIR, TARGET_NAME)
        if not os.path.exists(raw_exe):
            print(f"[ERROR] No se encontró el binario generado en {raw_exe}")
            sys.exit(1)
        print(f"[2/3] Generando binario con target triple para Tauri: {TARGET_NAME}")
        shutil.copy2(raw_exe, triple_exe)
        dest_binary = raw_exe
    else:
        dist_dir = os.path.join(BINARIES_DIR, "miku-core")
        raw_exe = os.path.join(dist_dir, "miku-core.exe")
        triple_dir = os.path.join(BINARIES_DIR, "miku-core-x86_64-pc-windows-msvc")
        triple_exe = os.path.join(BINARIES_DIR, TARGET_NAME)
        if not os.path.exists(raw_exe):
            print(f"[ERROR] No se encontró la carpeta del servidor generada en {dist_dir}")
            sys.exit(1)
        print(f"[2/3] Sincronizando carpeta del servidor para Tauri: {triple_dir}")
        if os.path.exists(triple_dir):
            shutil.rmtree(triple_dir, onerror=_remove_readonly)
        shutil.copytree(dist_dir, triple_dir)
        # Asegurar binario con target triple para validación de Tauri externalBin
        shutil.copy2(raw_exe, triple_exe)
        dest_binary = raw_exe

    # Sincronizar con AppData\Local\Miku Desktop para arranque instantáneo (1s) sin descompresión
    if LOCAL_APP_DIR:
        print(f"[3/3] Sincronizando con {LOCAL_APP_DIR}...")
        try:
            os.makedirs(LOCAL_APP_DIR, exist_ok=True)
            if is_onefile:
                shutil.copy2(raw_exe, os.path.join(LOCAL_APP_DIR, "miku-core.exe"))
            else:
                dest_local_dir = os.path.join(LOCAL_APP_DIR, "miku-core")
                if os.path.exists(dest_local_dir):
                    shutil.rmtree(dest_local_dir, onerror=_remove_readonly)
                shutil.copytree(dist_dir, dest_local_dir)
                shutil.copy2(raw_exe, os.path.join(LOCAL_APP_DIR, "miku-core.exe"))
            print(f"[OK] Sincronizado exitosamente a {LOCAL_APP_DIR}")
        except Exception as e:
            print(f"[AVISO] No se pudo copiar directamente a {LOCAL_APP_DIR}: {e}")

    print("=" * 60)
    print("[EXITO] Compilación de carpetas y binario de Miku Core finalizada!")
    print(f"Ubicación: {triple_exe}")
    print("=" * 60)

if __name__ == "__main__":
    run()
