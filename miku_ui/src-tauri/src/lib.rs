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
            if let Some(window) = app.get_webview_window("main") {
                if let Ok(Some(monitor)) = window.current_monitor() {
                    let sf = monitor.scale_factor();
                    let screen_w = monitor.size().width as f64 / sf;
                    let init_w = 340.0;
                    let init_h = 50.0;
                    let x_pos = (screen_w - init_w) / 2.0;
                    let _ = window.set_size(tauri::Size::Logical(tauri::LogicalSize::new(init_w, init_h)));
                    let _ = window.set_position(tauri::Position::Logical(tauri::LogicalPosition::new(x_pos, 0.0)));
                }
            }

            let config_i = MenuItem::with_id(app, "config", "Configuración (API Keys)", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "Salir", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&config_i, &quit_i])?;

            TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "config" => {
                        open_settings_window(app.clone());
                    }
                    "quit" => {
                        stop_speech_silent();
                        std::process::exit(0);
                    }
                    _ => {}
                })
                .build(app)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if window.label() == "main" {
                if let tauri::WindowEvent::Focused(focused) = event {
                    if !focused {
                        let _ = window.emit("window-blur", ());
                    }
                }
                if let tauri::WindowEvent::Destroyed = event {
                    stop_speech_silent();
                }
            }
            if window.label() == "settings" {
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
            check_update,
            install_update
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
