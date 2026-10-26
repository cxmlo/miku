use std::sync::atomic::{AtomicBool, Ordering};
static IGNORE_STATE: AtomicBool = AtomicBool::new(false);

#[tauri::command]
fn check_and_set_click_through(window: tauri::Window, global_mouse_x: f64, global_mouse_y: f64, isl_left: f64, isl_top: f64, isl_right: f64, isl_bottom: f64) {
    if let Ok(origin) = window.outer_position() {
        let scale = window.scale_factor().unwrap_or(1.0);
        let win_rel_x = (global_mouse_x - origin.x as f64) / scale;
        let win_rel_y = (global_mouse_y - origin.y as f64) / scale;
        
        let margin = 14.0; // Perdonar unos píxeles alrededor de Miku
        let inside = win_rel_x >= isl_left - margin
            && win_rel_x <= isl_right + margin
            && win_rel_y >= isl_top - margin
            && win_rel_y <= isl_bottom + margin;
            
        let should_ignore = !inside;
        if should_ignore != IGNORE_STATE.load(Ordering::Relaxed) {
            let _ = window.set_ignore_cursor_events(should_ignore);
            IGNORE_STATE.store(should_ignore, Ordering::Relaxed);
        }
    }
}

#[tauri::command]
fn position_top_center(window: tauri::Window) {
    if let Ok(Some(monitor)) = window.current_monitor() {
        let sf = monitor.scale_factor();
        let screen_w = monitor.size().width as f64 / sf;
        let _ = window.set_size(tauri::Size::Logical(tauri::LogicalSize::new(800.0, 500.0)));
        let _ = window.set_position(tauri::Position::Logical(tauri::LogicalPosition::new((screen_w - 800.0) / 2.0, 0.0)));
    }
}

#[tauri::command]
fn resize_window(window: tauri::Window, width: f64, height: f64) {
    if let Ok(Some(monitor)) = window.current_monitor() {
        let sf = monitor.scale_factor();
        let screen_w = monitor.size().width as f64 / sf;
        let x_pos = (screen_w - width) / 2.0;
        let _ = window.set_size(tauri::Size::Logical(tauri::LogicalSize::new(width, height)));
        let _ = window.set_position(tauri::Position::Logical(tauri::LogicalPosition::new(x_pos, 0.0)));
    }
}

#[tauri::command]
fn get_cursor_position() -> (f64, f64) {
    #[repr(C)]
    struct POINT { x: i32, y: i32 }
    extern "system" {
        fn GetCursorPos(lpPoint: *mut POINT) -> i32;
    }
    let mut pt = POINT { x: 0, y: 0 };
    unsafe { GetCursorPos(&mut pt); }
    (pt.x as f64, pt.y as f64)
}

#[tauri::command]
fn close_settings(app: tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("settings") {
        let _ = win.hide();
    }
}

#[tauri::command]
fn minimize_settings(app: tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("settings") {
        let _ = win.minimize();
    }
}

#[tauri::command]
async fn check_update(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    use tauri_plugin_updater::UpdaterExt;
    let updater = app.updater().map_err(|e| e.to_string())?;
    match updater.check().await {
        Ok(Some(update)) => Ok(serde_json::json!({
            "available": true,
            "version": update.version,
            "body": update.body.clone().unwrap_or_default(),
            "date": update.date.map(|d| d.to_string()).unwrap_or_default()
        })),
        Ok(None) => Ok(serde_json::json!({
            "available": false
        })),
        Err(e) => {
            let err_msg = e.to_string();
            if err_msg.contains("404") || err_msg.to_lowercase().contains("not found") {
                Ok(serde_json::json!({
                    "available": false,
                    "latest": true
                }))
            } else {
                Err(err_msg)
            }
        }
    }
}

#[tauri::command]
async fn install_update(app: tauri::AppHandle) -> Result<String, String> {
    use tauri_plugin_updater::UpdaterExt;
    let updater = app.updater().map_err(|e| e.to_string())?;
    if let Some(update) = updater.check().await.map_err(|e| e.to_string())? {
        update.download_and_install(|_chunk_length, _content_length| {}, || {}).await.map_err(|e| e.to_string())?;
        app.restart();
    }
    Ok("no_update".into())
}

use std::sync::Mutex;
use std::process::Child;
use std::net::TcpStream;
use std::path::{Path, PathBuf};

static BACKEND_CHILD: Mutex<Option<Child>> = Mutex::new(None);

fn is_port_open(port: u16) -> bool {
    TcpStream::connect(("127.0.0.1", port)).is_ok()
}

fn start_backend() {
    if is_port_open(8000) {
        eprintln!("[INFO] Miku Core backend port 8000 is already active.");
        return;
    }

    let current_exe = std::env::current_exe().unwrap_or_default();
    let exe_dir = current_exe.parent().unwrap_or_else(|| Path::new(""));

    let try_python = || -> bool {
        let mut search_dirs = Vec::new();
        search_dirs.push(exe_dir.to_path_buf());
        if let Some(p1) = exe_dir.parent() { search_dirs.push(p1.to_path_buf()); }
        if let Some(p2) = exe_dir.parent().and_then(|p| p.parent()) { search_dirs.push(p2.to_path_buf()); }
        if let Some(p3) = exe_dir.parent().and_then(|p| p.parent()).and_then(|p| p.parent()) { search_dirs.push(p3.to_path_buf()); }
        search_dirs.push(PathBuf::from(r"c:\Users\cxmluwu\Desktop\pryecto mascota\miku V2"));

        for dir in search_dirs {
            let server_py = dir.join("server.py");
            if server_py.exists() {
                let venv_pythonw = dir.join("venv").join("Scripts").join("pythonw.exe");
                let venv_python = dir.join("venv").join("Scripts").join("python.exe");
                let python_bin = if venv_pythonw.exists() {
                    venv_pythonw
                } else if venv_python.exists() {
                    venv_python
                } else {
                    PathBuf::from("python")
                };

                eprintln!("[INFO] Starting Miku server via Python: {:?} (working dir: {:?})", python_bin, dir);
                let mut cmd = std::process::Command::new(python_bin);
                cmd.arg("server.py");
                cmd.current_dir(&dir);
                #[cfg(target_os = "windows")]
                {
                    use std::os::windows::process::CommandExt;
                    cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
                }
                match cmd.spawn() {
                    Ok(child) => {
                        if let Ok(mut lock) = BACKEND_CHILD.lock() {
                            *lock = Some(child);
                        }
                        return true;
                    }
                    Err(e) => {
                        eprintln!("[ERROR] Failed to start server.py: {:?}", e);
                    }
                }
            }
        }
        false
    };

    let try_sidecar = || -> bool {
        let sidecar_candidates = [
            exe_dir.join("miku-core").join("miku-core.exe"),
            exe_dir.join("binaries").join("miku-core").join("miku-core.exe"),
            exe_dir.join("binaries").join("miku-core-x86_64-pc-windows-msvc").join("miku-core.exe"),
            exe_dir.join("miku-core.exe"),
            exe_dir.join("binaries").join("miku-core-x86_64-pc-windows-msvc.exe"),
            exe_dir.join("resources").join("miku-core.exe"),
            exe_dir.join("resources").join("miku-core").join("miku-core.exe"),
        ];

        for sidecar in &sidecar_candidates {
            if sidecar.exists() {
                eprintln!("[INFO] Starting Miku Core sidecar binary: {:?}", sidecar);
                let mut cmd = std::process::Command::new(sidecar);
                let run_dir = sidecar.parent().unwrap_or(exe_dir);
                cmd.current_dir(run_dir);
                #[cfg(target_os = "windows")]
                {
                    use std::os::windows::process::CommandExt;
                    cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
                }
                match cmd.spawn() {
                    Ok(child) => {
                        if let Ok(mut lock) = BACKEND_CHILD.lock() {
                            *lock = Some(child);
                        }
                        return true;
                    }
                    Err(e) => {
                        eprintln!("[ERROR] Failed to spawn sidecar: {:?}", e);
                    }
                }
            }
        }
        false
    };

    #[cfg(debug_assertions)]
    {
        if try_python() || try_sidecar() {
            return;
        }
    }

    #[cfg(not(debug_assertions))]
    {
        if try_sidecar() || try_python() {
            return;
        }
    }

    eprintln!("[WARN] Could not find miku-core.exe or server.py to start backend.");
}

fn stop_backend() {
    stop_speech_silent();

    // 1. Solicitud de apagado limpio al Gateway FastAPI
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        let mut cmd = std::process::Command::new("powershell");
        cmd.args(["-NoProfile", "-WindowStyle", "Hidden", "-Command", "Invoke-RestMethod -Uri http://127.0.0.1:8000/api/system/shutdown -Method Post -Headers @{'x-api-key'='miku_secure_key_2026'} -TimeoutSec 1 -ErrorAction SilentlyContinue"]);
        cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
        let _ = cmd.spawn();
    }
    #[cfg(not(target_os = "windows"))]
    {
        let _ = std::process::Command::new("curl")
            .args(["-s", "-X", "POST", "-H", "x-api-key: miku_secure_key_2026", "http://127.0.0.1:8000/api/system/shutdown"])
            .spawn();
    }

    // 2. Terminar proceso hijo si fue iniciado por Tauri
    if let Ok(mut lock) = BACKEND_CHILD.lock() {
        if let Some(mut child) = lock.take() {
            let _ = child.kill();
        }
    }

    // 3. Garantizar que ningún proceso huérfano de miku-core.exe quede bloqueando en Windows
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        let mut kill_cmd = std::process::Command::new("taskkill");
        kill_cmd.args(["/F", "/IM", "miku-core.exe", "/T"]);
        kill_cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
        let _ = kill_cmd.status();
    }
}

fn stop_speech_silent() {
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        let mut cmd = std::process::Command::new("powershell");
        cmd.args(["-NoProfile", "-WindowStyle", "Hidden", "-Command", "Invoke-RestMethod -Uri http://127.0.0.1:8000/api/speech/stop -Method Post -TimeoutSec 1 -ErrorAction SilentlyContinue"]);
        cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
        let _ = cmd.spawn();
    }
    #[cfg(not(target_os = "windows"))]
    {
        let _ = std::process::Command::new("curl")
            .args(["-s", "-X", "POST", "http://127.0.0.1:8000/api/speech/stop"])
            .spawn();
    }
}

#[tauri::command]
fn open_settings_window(app: tauri::AppHandle) {
    if let Some(existing) = app.get_webview_window("settings") {
        let _ = existing.show();
        let _ = existing.set_focus();
        return;
    }
    let builder = tauri::WebviewWindowBuilder::new(
        &app,
        "settings",
        tauri::WebviewUrl::App("miku_settings.html".into())
    )
    .title("Configuración · Miku")
    .inner_size(1080.0, 780.0)
    .min_inner_size(760.0, 600.0)
    .decorations(false)
    .transparent(true)
    .shadow(false)
    .resizable(false)
    .center();

    match builder.build() {
        Ok(win) => {
            if let Some(icon) = app.default_window_icon() {
                let _ = win.set_icon(icon.clone());
            }
            let _ = win.show();
            let _ = win.set_focus();
        }
        Err(e) => {
            eprintln!("[ERROR] Failed to build settings window: {:?}", e);
        }
    }
}

#[tauri::command]
fn open_settings(app: tauri::AppHandle) {
    open_settings_window(app);
}

#[tauri::command]
fn open_link_window(app: tauri::AppHandle) {
    if let Some(existing) = app.get_webview_window("link") {
        let _ = existing.show();
        let _ = existing.set_focus();
        return;
    }
    let builder = tauri::WebviewWindowBuilder::new(
        &app,
        "link",
        tauri::WebviewUrl::App("miku_link.html".into())
    )
    .title("Miku-Link · Enlace Móvil")
    .inner_size(460.0, 700.0)
    .decorations(false)
    .transparent(true)
    .shadow(false)
    .resizable(false)
    .center();

    if let Ok(win) = builder.build() {
        if let Some(icon) = app.default_window_icon() {
            let _ = win.set_icon(icon.clone());
        }
        let _ = win.show();
        let _ = win.set_focus();
    }
}

#[tauri::command]
fn close_link(app: tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("link") {
        let _ = win.hide();
    }
}

#[tauri::command]
fn hide_main_window(app: tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        let _ = win.hide();
    }
}

use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Emitter, Manager,
};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    #[cfg(target_os = "windows")]
    {
        extern "system" {
            fn CreateMutexW(lpMutexAttributes: *mut std::ffi::c_void, bInitialOwner: i32, lpName: *const u16) -> *mut std::ffi::c_void;
            fn GetLastError() -> u32;
            fn FindWindowW(lpClassName: *const u16, lpWindowName: *const u16) -> isize;
            fn SetForegroundWindow(hWnd: isize) -> i32;
            fn ShowWindow(hWnd: isize, nCmdShow: i32) -> i32;
        }
        use std::os::windows::ffi::OsStrExt;
        let mutex_name: Vec<u16> = std::ffi::OsStr::new("Global\\MikuDynamicIslandSingleInstanceMutex")
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();
        let _mutex = unsafe { CreateMutexW(std::ptr::null_mut(), 0, mutex_name.as_ptr()) };
        if unsafe { GetLastError() } == 183 { // ERROR_ALREADY_EXISTS
            eprintln!("[INFO] Miku ya está en ejecución. Enfocando ventana activa...");
            let win_title: Vec<u16> = std::ffi::OsStr::new("Miku · Dynamic Island")
                .encode_wide()
                .chain(std::iter::once(0))
                .collect();
            let hwnd = unsafe { FindWindowW(std::ptr::null(), win_title.as_ptr()) };
            if hwnd != 0 {
                unsafe {
                    ShowWindow(hwnd, 9); // SW_RESTORE
                    SetForegroundWindow(hwnd);
                }
            }
            return;
        }
    }

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            // Auto-iniciar el servidor Core si no está activo
            start_backend();

            if let Some(window) = app.get_webview_window("main") {
                let monitor = window
                    .primary_monitor()
                    .ok()
                    .flatten()
                    .or_else(|| window.current_monitor().ok().flatten());
                if let Some(monitor) = monitor {
                    let sf = monitor.scale_factor();
                    let init_w = 440.0;
                    let init_h = 50.0;
                    let monitor_position = monitor.position();
                    let monitor_size = monitor.size();
                    let x_pos = monitor_position.x as f64 / sf
                        + (monitor_size.width as f64 / sf - init_w) / 2.0;
                    let y_pos = monitor_position.y as f64 / sf;
                    let _ = window.set_size(tauri::Size::Logical(tauri::LogicalSize::new(init_w, init_h)));
                    let _ = window.set_position(tauri::Position::Logical(tauri::LogicalPosition::new(x_pos, y_pos)));
                }
                let _ = window.show();
            }

            let open_i = MenuItem::with_id(app, "open", "Abrir Isla Dinámica", true, None::<&str>)?;
            let hide_i = MenuItem::with_id(app, "hide", "Ocultar Isla (Ahorro Energía)", true, None::<&str>)?;
            let link_i = MenuItem::with_id(app, "link", "Miku-Link (Enlace Móvil)", true, None::<&str>)?;
            let low_cost_i = MenuItem::with_id(app, "low_cost", "🔴 Modo Ahorro: Desactivado", true, None::<&str>)?;
            let config_i = MenuItem::with_id(app, "config", "Configuración (API Keys)", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "Salir", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&open_i, &hide_i, &link_i, &low_cost_i, &config_i, &quit_i])?;

            let low_cost_item_clone = low_cost_i.clone();
            TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .on_menu_event(move |app, event| match event.id.as_ref() {
                    "open" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "hide" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.hide();
                        }
                        let _ = low_cost_item_clone.set_text("🟢 Modo Ahorro: Activado");
                        #[cfg(target_os = "windows")]
                        {
                            use std::os::windows::process::CommandExt;
                            let mut cmd = std::process::Command::new("powershell");
                            cmd.args(["-NoProfile", "-WindowStyle", "Hidden", "-Command", "Invoke-RestMethod -Uri http://127.0.0.1:8000/api/settings/low_cost_toggle -Method Post -TimeoutSec 2 -ErrorAction SilentlyContinue"]);
                            cmd.creation_flags(0x08000000);
                            let _ = cmd.spawn();
                        }
                    }
                    "link" => {
                        open_link_window(app.clone());
                    }
                    "low_cost" => {
                        static IS_LOW: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);
                        let next = !IS_LOW.load(std::sync::atomic::Ordering::Relaxed);
                        IS_LOW.store(next, std::sync::atomic::Ordering::Relaxed);
                        let _ = low_cost_item_clone.set_text(if next { "🟢 Modo Ahorro: Activado" } else { "🔴 Modo Ahorro: Desactivado" });
                        #[cfg(target_os = "windows")]
                        {
                            use std::os::windows::process::CommandExt;
                            let mut cmd = std::process::Command::new("powershell");
                            cmd.args(["-NoProfile", "-WindowStyle", "Hidden", "-Command", "Invoke-RestMethod -Uri http://127.0.0.1:8000/api/settings/low_cost_toggle -Method Post -TimeoutSec 2 -ErrorAction SilentlyContinue"]);
                            cmd.creation_flags(0x08000000);
                            let _ = cmd.spawn();
                        }
                    }
                    "config" => {
                        open_settings_window(app.clone());
                    }
                    "quit" => {
                        stop_backend();
                        std::process::exit(0);
                    }
                    _ => {}
                })
                .build(app)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if window.label() == "main" {
                match event {
                    tauri::WindowEvent::Focused(focused) => {
                        if !focused {
                            let _ = window.emit("window-blur", ());
                        }
                    }
                    tauri::WindowEvent::CloseRequested { api, .. } => {
                        let _ = window.hide();
                        api.prevent_close();
                    }
                    tauri::WindowEvent::Destroyed => stop_backend(),
                    _ => {}
                }
            }
            if window.label() == "settings" {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    let _ = window.hide();
                    api.prevent_close();
                }
            }
            if window.label() == "link" {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    let _ = window.hide();
                    api.prevent_close();
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            check_and_set_click_through,
            position_top_center,
            resize_window,
            get_cursor_position,
            open_settings_window,
            open_settings,
            close_settings,
            minimize_settings,
            open_link_window,
            close_link,
            hide_main_window,
            check_update,
            install_update
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
